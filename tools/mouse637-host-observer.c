/* External, read-only Mac process accounting. Never linked into Mouse. */
#define _DARWIN_C_SOURCE 1
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <signal.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <time.h>
#include <unistd.h>
#ifdef __APPLE__
#include <libproc.h>
#include <mach/mach.h>
#include <mach/mach_time.h>
#include <sys/sysctl.h>
#include <sys/utsname.h>
#endif

#define MAX_OWNED 256
#define MAX_IMAGES 512
#define MAX_RECORDS 65536
#define MAX_OUTPUT (64u * 1024u * 1024u)
#define PATH_BYTES 4096
#define INTERVAL_MS 250

typedef struct {
  int pid, ppid, uid, status;
  uint64_t start_sec, start_usec, start_abs;
  uint64_t user, system, runnable;
  unsigned char uuid[16];
  char path[PATH_BYTES];
} Process;

typedef struct {
  int owner;
  char path[PATH_BYTES];
  unsigned char uuid[16];
} Image;

typedef struct {
  Process birth;
  int parent_index, initial_image, image, last_ppid;
  bool alive;
} Owned;

enum Kind { IDENTITY = 1, SAMPLE, HOST, EXITED, REPARENTED, REUSED, IMAGE_CHANGED, ERROR_RECORD };
typedef struct {
  enum Kind kind;
  int index, code, other, image;
  uint64_t begin, end, scheduled, values[6];
} Record;

typedef struct {
  uint64_t (*now)(void *);
  int (*read)(void *, int, Process *);
  int (*children)(void *, int, int *, size_t);
  int (*host)(void *, uint32_t[4], uint64_t *, uint64_t *);
  int (*self)(void *, uint64_t *, uint64_t *);
  void (*sleep_until)(void *, uint64_t);
  void *context;
} Ops;

typedef struct {
  Ops ops;
  Owned owned[MAX_OWNED];
  Image images[MAX_IMAGES];
  Record *records;
  size_t owned_count, image_count, count;
  uint64_t numer, denom, begin, end, deadline, interval, missed;
  uint64_t max_read_ticks, max_lag_ticks, self_user_us, self_system_us;
  uint64_t discovery_gone, discovery_moved;
  uint64_t launch_before_us, launch_after_us, budget_ms;
  int root_pid, parent_pid, uid, sampler_pid, logical_cpus;
  char phase[16], nonce[65], root_path[PATH_BYTES], output[PATH_BYTES];
  char kernel[128], machine[64];
  bool ok, root_gone;
  bool within_self_cpu_limit;
  const char *reason;
  int error_code;
} State;

static volatile sig_atomic_t stop_requested;
static void stop_signal(int sig) { (void)sig; stop_requested = 1; }

static bool same_birth(const Process *a, const Process *b) {
  return a->pid == b->pid && a->uid == b->uid &&
    a->start_sec == b->start_sec && a->start_usec == b->start_usec &&
    a->start_abs == b->start_abs;
}

static bool same_image(const Image *a, const Process *b) {
  return strcmp(a->path, b->path) == 0 && memcmp(a->uuid, b->uuid, 16) == 0;
}

static int child_count_result(int count, int error) {
  /* libproc maps a failed __proc_info call to zero and leaves errno set. */
  return count<0 || (count==0 && error!=0) ? -(error?error:EIO) : count;
}

static uint64_t ticks_for_ms(const State *s, uint64_t ms) {
  return (uint64_t)(((__uint128_t)ms * 1000000u * s->denom) / s->numer);
}

static bool self_cpu_within_limit(const State *s) {
  if (s->end<=s->begin || !s->numer || !s->denom) return false;
  __uint128_t cpu=(__uint128_t)s->self_user_us+s->self_system_us;
  return cpu*1000u*100u*s->denom <= (__uint128_t)(s->end-s->begin)*s->numer;
}

static void fail(State *s, const char *reason, int code) {
  if (s->ok) { s->reason = reason; s->error_code = code; }
  s->ok = false;
}

static bool record(State *s, Record r) {
  if (s->count >= MAX_RECORDS) { fail(s, "record-cap", EOVERFLOW); return false; }
  s->records[s->count++] = r;
  if (r.end >= r.begin && r.end - r.begin > s->max_read_ticks)
    s->max_read_ticks = r.end - r.begin;
  return true;
}

static int read_process(State *s, int pid, Process *p, uint64_t *begin, uint64_t *end) {
  *begin = s->ops.now(s->ops.context);
  memset(p, 0, sizeof(*p));
  int error = s->ops.read(s->ops.context, pid, p);
  *end = s->ops.now(s->ops.context);
  if (*end < *begin) return EDOM;
  if (!error && (p->pid != pid || p->uid != s->uid || p->start_usec >= 1000000u ||
                 !p->start_sec || !p->start_abs || p->start_abs > *end || !p->path[0])) return EPROTO;
  return error;
}

static int add_image(State *s, int owner, const Process *p) {
  if (s->image_count >= MAX_IMAGES) { fail(s, "image-cap", EOVERFLOW); return -1; }
  int index = (int)s->image_count++;
  Image *image = &s->images[index];
  image->owner = owner;
  memcpy(image->path, p->path, sizeof(image->path));
  memcpy(image->uuid, p->uuid, 16);
  return index;
}

static int add_owned(State *s, const Process *p, int parent, uint64_t begin, uint64_t end) {
  if (s->owned_count >= MAX_OWNED) { fail(s, "owned-cap", EOVERFLOW); return -1; }
  int index = (int)s->owned_count++;
  Owned *owned = &s->owned[index];
  owned->birth = *p;
  owned->parent_index = parent;
  owned->last_ppid = p->ppid;
  owned->alive = true;
  owned->image = owned->initial_image = add_image(s, index, p);
  if (owned->image < 0) return -1;
  record(s, (Record){.kind=IDENTITY,.index=index,.begin=begin,.end=end,.image=owned->image});
  return index;
}

static int known_pid(const State *s, int pid) {
  for (size_t i = 0; i < s->owned_count; ++i)
    if (s->owned[i].alive && s->owned[i].birth.pid == pid) return (int)i;
  return -1;
}

static bool inspect_owned(State *s, int index, Process *p, bool emit_sample) {
  Owned *owned = &s->owned[index];
  if (!owned->alive) return false;
  uint64_t begin, end;
  int error = read_process(s, owned->birth.pid, p, &begin, &end);
  if (error == ESRCH || error == ENOENT) {
    owned->alive = false;
    record(s, (Record){.kind=EXITED,.index=index,.begin=begin,.end=end,.code=error});
    if (index == 0) s->root_gone = true;
    return false;
  }
  if (error) {
    record(s, (Record){.kind=ERROR_RECORD,.index=index,.begin=begin,.end=end,.code=error});
    fail(s, "process-read", error); return false;
  }
  if (!same_birth(&owned->birth, p)) {
    owned->alive = false;
    record(s, (Record){.kind=REUSED,.index=index,.begin=begin,.end=end,
      .values={p->start_sec,p->start_usec,p->start_abs}});
    if (index == 0) fail(s, "root-identity-changed", EPROTO);
    return false;
  }
  if (p->ppid != owned->last_ppid) {
    record(s, (Record){.kind=REPARENTED,.index=index,.begin=begin,.end=end,
      .other=p->ppid,.code=owned->last_ppid});
    owned->last_ppid = p->ppid;
  }
  if (!same_image(&s->images[owned->image], p)) {
    if (index == 0) { fail(s, "root-image-changed", EPROTO); return false; }
    int image = add_image(s, index, p);
    if (image < 0) return false;
    owned->image = image;
    record(s, (Record){.kind=IMAGE_CHANGED,.index=index,.begin=begin,.end=end,.image=image});
  }
  if (emit_sample)
    record(s, (Record){.kind=SAMPLE,.index=index,.begin=begin,.end=end,.image=owned->image,
      .values={p->user,p->system,p->runnable,p->start_abs}});
  return true;
}

static void discover(State *s, int parent) {
  Process verified;
  if (!inspect_owned(s, parent, &verified, false) || !s->ok) return;
  int pids[MAX_OWNED + 1];
  int n = s->ops.children(s->ops.context, verified.pid, pids, MAX_OWNED + 1);
  if (n < 0) {
    if ((n==-ESRCH || n==-ENOENT) && !inspect_owned(s,parent,&verified,false) &&
        !s->owned[parent].alive) return;
    fail(s, "children-read", -n); return;
  }
  if (n >= MAX_OWNED + 1) { fail(s, "children-cap", EOVERFLOW); return; }
  /* Revalidate the parent after enumeration. PID reuse cannot adopt a tree. */
  if (!inspect_owned(s, parent, &verified, false) || !s->ok) return;
  for (int j = 0; j < n && s->ok; ++j) {
    if (pids[j] <= 0 || pids[j] == s->sampler_pid || known_pid(s, pids[j]) >= 0) continue;
    Process child; uint64_t begin, end;
    int error = read_process(s, pids[j], &child, &begin, &end);
    if (error == ESRCH || error == ENOENT) { ++s->discovery_gone; continue; }
    if (error) { fail(s, "child-identity-read", error); break; }
    if (child.ppid != verified.pid) { ++s->discovery_moved; continue; }
    Process parent_again;
    if (!inspect_owned(s, parent, &parent_again, false) || !s->ok) break;
    if (child.start_abs < parent_again.start_abs) { fail(s, "child-precedes-parent", EPROTO); break; }
    add_owned(s, &child, parent, begin, end);
  }
}

static void sample_cycle(State *s, uint64_t scheduled) {
  uint64_t begin = s->ops.now(s->ops.context);
  uint32_t ticks[4] = {0}; uint64_t user = 0, system = 0;
  int error = s->ops.host(s->ops.context, ticks, &user, &system);
  uint64_t end = s->ops.now(s->ops.context);
  if (error || end < begin) { fail(s, "host-read", error ? error : EDOM); return; }
  s->self_user_us = user; s->self_system_us = system;
  uint64_t lag = begin > scheduled ? begin - scheduled : 0;
  if (lag > s->max_lag_ticks) s->max_lag_ticks = lag;
  record(s, (Record){.kind=HOST,.begin=begin,.end=end,.scheduled=scheduled,
    .values={ticks[0],ticks[1],ticks[2],ticks[3],user,system}});
  for (size_t i = 0; i < s->owned_count && s->ok; ++i) {
    Process p;
    inspect_owned(s, (int)i, &p, true);
    if (i == 0 && s->root_gone) return;
    if (s->owned[i].alive) discover(s, (int)i);
  }
}

static bool initialize_root(State *s) {
  Process p; uint64_t begin, end;
  int error = read_process(s, s->root_pid, &p, &begin, &end);
  if (error) { fail(s, "root-initial-read", error); return false; }
  __uint128_t start_us = (__uint128_t)p.start_sec * 1000000u + p.start_usec;
  if (p.ppid != s->parent_pid || strcmp(p.path, s->root_path) ||
      start_us < s->launch_before_us || start_us > s->launch_after_us) {
    fail(s, "root-launch-identity", EPROTO); return false;
  }
  s->begin = begin;
  s->interval = ticks_for_ms(s, INTERVAL_MS);
  uint64_t duration = ticks_for_ms(s, s->budget_ms);
  if (!s->interval || !duration || UINT64_MAX - p.start_abs < duration) {
    fail(s, "clock-overflow", EOVERFLOW); return false;
  }
  /* Birth plus the original budget is conservative relative to run_logged. */
  s->deadline = p.start_abs + duration;
  return add_owned(s, &p, -1, begin, end) == 0 && s->ok;
}

static void observe(State *s) {
  if (!initialize_root(s)) { s->end = s->ops.now(s->ops.context); return; }
  uint64_t next = s->ops.now(s->ops.context);
  while (s->ok && !s->root_gone && !stop_requested) {
    uint64_t now = s->ops.now(s->ops.context);
    if (now >= s->deadline) { fail(s, "phase-budget", ETIMEDOUT); break; }
    sample_cycle(s, next);
    if (!s->ok || s->root_gone) break;
    now = s->ops.now(s->ops.context);
    uint64_t advance = now >= next ? (now - next) / s->interval + 1u : 1u;
    s->missed += advance - 1u;
    if (advance > (UINT64_MAX - next) / s->interval) { fail(s, "clock-overflow", EOVERFLOW); break; }
    next += advance * s->interval;
    s->ops.sleep_until(s->ops.context, next < s->deadline ? next : s->deadline);
  }
  if (stop_requested && !s->root_gone) fail(s, "stop-requested", EINTR);
  if (s->ok && s->root_gone) s->reason = "root-exited";
  int self_error=s->ops.self(s->ops.context,&s->self_user_us,&s->self_system_us);
  if (self_error) fail(s,"self-read",self_error);
  s->end = s->ops.now(s->ops.context);
  s->within_self_cpu_limit=self_cpu_within_limit(s);
  if (s->ok && !s->within_self_cpu_limit) fail(s,"self-cpu-budget",EOVERFLOW);
}

static bool quote(char *out, size_t cap, const char *value) {
  size_t n = 0;
  if (cap < 3) return false;
  out[n++] = '"';
  for (const unsigned char *p = (const unsigned char *)value; *p; ++p) {
    if (n + 7 >= cap) return false;
    if (*p == '"' || *p == '\\') { out[n++] = '\\'; out[n++] = (char)*p; }
    else if (*p < 32) { int added = snprintf(out + n, cap - n, "\\u%04x", *p); n += (size_t)added; }
    else out[n++] = (char)*p;
  }
  out[n++] = '"'; out[n] = 0; return true;
}

static void uuid_hex(const unsigned char uuid[16], char out[33]) {
  for (int i = 0; i < 16; ++i) (void)snprintf(out + 2*i, 3, "%02x", uuid[i]);
  out[32] = 0;
}

static bool line(FILE *out, size_t *bytes, const char *format, ...) {
  char buffer[32768];
  va_list args; va_start(args, format);
  int n = vsnprintf(buffer, sizeof(buffer), format, args); va_end(args);
  if (n < 0 || (size_t)n >= sizeof(buffer) || *bytes + (size_t)n + 4096u > MAX_OUTPUT) return false;
  if (fwrite(buffer, 1, (size_t)n, out) != (size_t)n) return false;
  *bytes += (size_t)n; return true;
}

static bool dump(State *s, FILE *out) {
  size_t bytes = 0, written = 0;
  uint64_t dump_begin=s->ops.now(s->ops.context);
  char path[PATH_BYTES*6+3], kernel[800], machine[400];
  if (!quote(path,sizeof(path),s->root_path) || !quote(kernel,sizeof(kernel),s->kernel) ||
      !quote(machine,sizeof(machine),s->machine)) return false;
  if (!line(out,&bytes,"{\"type\":\"header\",\"sequence\":0,\"schema\":1,\"kind\":\"mouse637-host-observer\",\"phase\":\"%s\",\"nonce\":\"%s\",\"samplerPid\":%d,\"rootPid\":%d,\"expectedRootParentPid\":%d,\"uid\":%d,\"expectedRootPath\":%s,\"launchBeforeEpochUs\":%" PRIu64 ",\"launchAfterEpochUs\":%" PRIu64 ",\"budgetMs\":%" PRIu64 ",\"intervalMs\":250,\"limits\":{\"maxOwned\":256,\"maxImages\":512,\"maxRecords\":65536,\"maxOutputBytes\":67108864},\"clock\":\"mach_absolute_time\",\"counterUnits\":\"mach_absolute_time\",\"timebaseNumer\":%" PRIu64 ",\"timebaseDenom\":%" PRIu64 ",\"logicalCpus\":%d,\"kernel\":%s,\"machine\":%s}\n",s->phase,s->nonce,s->sampler_pid,s->root_pid,s->parent_pid,s->uid,path,s->launch_before_us,s->launch_after_us,s->budget_ms,s->numer,s->denom,s->logical_cpus,kernel,machine)) return false;
  for (size_t n=0;n<s->count;++n) {
    Record *r=&s->records[n]; bool good=false;
    if (r->kind==IDENTITY || r->kind==IMAGE_CHANGED) {
      const Owned *o=&s->owned[r->index]; const Image *im=&s->images[r->image]; char uuid[33];
      uuid_hex(im->uuid,uuid); if (!quote(path,sizeof(path),im->path)) return false;
      good=line(out,&bytes,"{\"type\":\"%s\",\"sequence\":%zu,\"identityIndex\":%d,\"imageIndex\":%d,\"pid\":%d,\"ppid\":%d,\"uid\":%d,\"parentIndex\":%d,\"startSec\":%" PRIu64 ",\"startUsec\":%" PRIu64 ",\"startAbstime\":%" PRIu64 ",\"uuid\":\"%s\",\"path\":%s,\"readStartMach\":%" PRIu64 ",\"readEndMach\":%" PRIu64 "}\n",r->kind==IDENTITY?"identity":"image",n+1,r->index,r->image,o->birth.pid,o->birth.ppid,o->birth.uid,o->parent_index,o->birth.start_sec,o->birth.start_usec,o->birth.start_abs,uuid,path,r->begin,r->end);
    } else if (r->kind==SAMPLE) {
      good=line(out,&bytes,"{\"type\":\"sample\",\"sequence\":%zu,\"identityIndex\":%d,\"imageIndex\":%d,\"readStartMach\":%" PRIu64 ",\"readEndMach\":%" PRIu64 ",\"userTime\":%" PRIu64 ",\"systemTime\":%" PRIu64 ",\"runnableTime\":%" PRIu64 ",\"startAbstime\":%" PRIu64 "}\n",n+1,r->index,r->image,r->begin,r->end,r->values[0],r->values[1],r->values[2],r->values[3]);
    } else if (r->kind==HOST) {
      good=line(out,&bytes,"{\"type\":\"host\",\"sequence\":%zu,\"scheduledMach\":%" PRIu64 ",\"readStartMach\":%" PRIu64 ",\"readEndMach\":%" PRIu64 ",\"cpuTicks\":[%" PRIu64 ",%" PRIu64 ",%" PRIu64 ",%" PRIu64 "],\"selfUserUs\":%" PRIu64 ",\"selfSystemUs\":%" PRIu64 "}\n",n+1,r->scheduled,r->begin,r->end,r->values[0],r->values[1],r->values[2],r->values[3],r->values[4],r->values[5]);
    } else {
      const char *type=r->kind==EXITED?"exit":r->kind==REPARENTED?"reparent":r->kind==REUSED?"reuse":"error";
      good=line(out,&bytes,"{\"type\":\"%s\",\"sequence\":%zu,\"identityIndex\":%d,\"readStartMach\":%" PRIu64 ",\"readEndMach\":%" PRIu64 ",\"code\":%d,\"otherPid\":%d,\"observedStartSec\":%" PRIu64 ",\"observedStartUsec\":%" PRIu64 ",\"observedStartAbstime\":%" PRIu64 "}\n",type,n+1,r->index,r->begin,r->end,r->code,r->other,r->values[0],r->values[1],r->values[2]);
    }
    if (!good) { fail(s,"output-cap-or-write",EIO); break; }
    ++written;
  }
  if (fflush(out)) fail(s,"data-flush",errno?errno:EIO);
  int self_error=s->ops.self(s->ops.context,&s->self_user_us,&s->self_system_us);
  uint64_t dump_end=s->ops.now(s->ops.context);
  if (self_error) fail(s,"final-self-read",self_error);
  s->within_self_cpu_limit=self_cpu_within_limit(s);
  if (s->ok&&!s->within_self_cpu_limit) fail(s,"self-cpu-budget",EOVERFLOW);
  /* Numerator includes startup, collection and flushed data serialization.
     The final EOF serialization/close residual is explicitly not measured. */
  return line(out,&bytes,"{\"type\":\"eof\",\"sequence\":%zu,\"ok\":%s,\"reason\":\"%s\",\"rootGone\":%s,\"errorCode\":%d,\"recordCount\":%zu,\"storedRecordCount\":%zu,\"droppedRecords\":%zu,\"ownedCount\":%zu,\"imageCount\":%zu,\"discoveryGone\":%" PRIu64 ",\"discoveryMoved\":%" PRIu64 ",\"samplingStartMach\":%" PRIu64 ",\"samplingEndMach\":%" PRIu64 ",\"observedDurationMach\":%" PRIu64 ",\"dumpStartMach\":%" PRIu64 ",\"dumpEndMach\":%" PRIu64 ",\"deadlineMach\":%" PRIu64 ",\"missedIntervals\":%" PRIu64 ",\"maxReadTicks\":%" PRIu64 ",\"maxLagTicks\":%" PRIu64 ",\"selfUserUs\":%" PRIu64 ",\"selfSystemUs\":%" PRIu64 ",\"selfCpuUs\":%" PRIu64 ",\"selfCpuAccounting\":\"startup+collection+flushed-data-before-eof\",\"unmeasuredResidual\":\"eof-write-close-free\",\"selfCpuLimitNumerator\":1,\"selfCpuLimitDenominator\":100,\"withinSelfCpuLimit\":%s,\"payloadBytesBeforeEOF\":%zu}\n",written+1,s->ok?"true":"false",s->reason?s->reason:"unknown",s->root_gone?"true":"false",s->error_code,written,s->count,s->count-written,s->owned_count,s->image_count,s->discovery_gone,s->discovery_moved,s->begin,s->end,s->end>=s->begin?s->end-s->begin:0,dump_begin,dump_end,s->deadline,s->missed,s->max_read_ticks,s->max_lag_ticks,s->self_user_us,s->self_system_us,s->self_user_us+s->self_system_us,s->within_self_cpu_limit?"true":"false",bytes);
}

#if defined(__APPLE__) && !defined(MOUSE_HOST_OBSERVER_TEST)
_Static_assert(CPU_STATE_MAX==4 && CPU_STATE_USER==0 && CPU_STATE_SYSTEM==1 && CPU_STATE_IDLE==2 && CPU_STATE_NICE==3,
               "Host CPU tick order changed");
typedef struct { mach_timebase_info_data_t timebase; } Mac;
static uint64_t mac_now(void *ctx) { (void)ctx; return mach_absolute_time(); }

static int mac_read(void *ctx, int pid, Process *out) {
  (void)ctx;
  struct proc_bsdinfo a,b;
  struct rusage_info_v4 usage;
  errno=0;
  if (proc_pidinfo(pid,PROC_PIDTBSDINFO,0,&a,sizeof(a)) != (int)sizeof(a)) return errno?errno:EPROTO;
  memset(&usage,0,sizeof(usage));
  if (proc_pid_rusage(pid,RUSAGE_INFO_V4,(rusage_info_t *)&usage)) return errno?errno:EIO;
  if (proc_pidpath(pid,out->path,sizeof(out->path)) <= 0) return errno?errno:EPROTO;
  out->path[sizeof(out->path)-1]=0;
  if (proc_pidinfo(pid,PROC_PIDTBSDINFO,0,&b,sizeof(b)) != (int)sizeof(b)) return errno?errno:EPROTO;
  if (a.pbi_pid!=b.pbi_pid || a.pbi_uid!=b.pbi_uid || a.pbi_start_tvsec!=b.pbi_start_tvsec || a.pbi_start_tvusec!=b.pbi_start_tvusec) return EAGAIN;
  out->pid=(int)b.pbi_pid; out->ppid=(int)b.pbi_ppid; out->uid=(int)b.pbi_uid; out->status=(int)b.pbi_status;
  out->start_sec=b.pbi_start_tvsec; out->start_usec=b.pbi_start_tvusec; out->start_abs=usage.ri_proc_start_abstime;
  out->user=usage.ri_user_time; out->system=usage.ri_system_time; out->runnable=usage.ri_runnable_time;
  memcpy(out->uuid,usage.ri_uuid,16);
  return 0;
}

static int mac_children(void *ctx, int pid, int *pids, size_t count) {
  (void)ctx; errno=0;
  int n=proc_listchildpids(pid,pids,(int)(count*sizeof(int)));
  return child_count_result(n,errno);
}

static int mac_self(void *ctx, uint64_t *user, uint64_t *system) {
  (void)ctx;
  struct rusage self;
  if (getrusage(RUSAGE_SELF,&self)) return errno?errno:EIO;
  *user=(uint64_t)self.ru_utime.tv_sec*1000000u+(uint64_t)self.ru_utime.tv_usec;
  *system=(uint64_t)self.ru_stime.tv_sec*1000000u+(uint64_t)self.ru_stime.tv_usec;
  return 0;
}

static int mac_host(void *ctx, uint32_t ticks[4], uint64_t *user, uint64_t *system) {
  (void)ctx;
  host_cpu_load_info_data_t load; mach_msg_type_number_t count=HOST_CPU_LOAD_INFO_COUNT;
  mach_port_t host=mach_host_self();
  kern_return_t result=host_statistics(host,HOST_CPU_LOAD_INFO,(host_info_t)&load,&count);
  (void)mach_port_deallocate(mach_task_self(),host);
  if (result!=KERN_SUCCESS || count!=HOST_CPU_LOAD_INFO_COUNT) return EIO;
  for (int i=0;i<4;++i) ticks[i]=(uint32_t)load.cpu_ticks[i];
  return mac_self(ctx,user,system);
}

static void mac_sleep(void *context, uint64_t until) {
  Mac *mac=context;
  while (!stop_requested) {
    uint64_t now=mach_absolute_time(); if (now>=until) return;
    uint64_t ns=(uint64_t)(((__uint128_t)(until-now)*mac->timebase.numer)/mac->timebase.denom);
    struct timespec delay={(time_t)(ns/1000000000u),(long)(ns%1000000000u)};
    if (!nanosleep(&delay,NULL) || errno!=EINTR) return;
  }
}

static bool number(const char *text, uint64_t *value) {
  char *end=NULL; errno=0;
  if (!text[0] || text[0]=='-' || text[0]=='+') return false;
  unsigned long long n=strtoull(text,&end,10);
  if (errno || !end || *end) return false;
  *value=(uint64_t)n; return true;
}

int main(int argc,char **argv) {
  if (argc!=11) { fprintf(stderr,"Usage: sampler PHASE ROOT_PID PARENT_PID ROOT_EXE BEFORE_US AFTER_US BUDGET_MS NONCE OUTPUT UID\n"); return 2; }
  State *s=calloc(1,sizeof(*s)); if (!s) return 2;
  s->records=calloc(MAX_RECORDS,sizeof(Record)); if (!s->records) { free(s); return 2; }
  uint64_t pid,ppid,uid;
  bool valid=number(argv[2],&pid)&&number(argv[3],&ppid)&&number(argv[5],&s->launch_before_us)&&
    number(argv[6],&s->launch_after_us)&&number(argv[7],&s->budget_ms)&&number(argv[10],&uid)&&
    pid>0&&pid<=INT_MAX&&ppid>0&&ppid<=INT_MAX&&uid<=INT_MAX&&s->launch_before_us<=s->launch_after_us&&
    strlen(argv[1])<sizeof(s->phase)&&strlen(argv[4])<sizeof(s->root_path)&&strlen(argv[9])<sizeof(s->output)&&strlen(argv[8])==64;
  for (const char *p=argv[8];valid&&*p;++p) valid=(*p>='0'&&*p<='9')||(*p>='a'&&*p<='f');
  valid=valid&&((!strcmp(argv[1],"baseline")&&s->budget_ms==900000)||(!strcmp(argv[1],"candidate")&&s->budget_ms==400000)||(!strcmp(argv[1],"fixture")&&s->budget_ms<=10000&&s->budget_ms>=500));
  if (!valid || (int)uid!=(int)geteuid() || (int)ppid!=(int)getppid()) { fprintf(stderr,"Invalid owned sampler configuration\n"); free(s->records); free(s); return 2; }
  snprintf(s->phase,sizeof(s->phase),"%s",argv[1]); snprintf(s->nonce,sizeof(s->nonce),"%s",argv[8]);
  snprintf(s->root_path,sizeof(s->root_path),"%s",argv[4]); snprintf(s->output,sizeof(s->output),"%s",argv[9]);
  s->root_pid=(int)pid;s->parent_pid=(int)ppid;s->uid=(int)uid;s->sampler_pid=(int)getpid();s->ok=true;s->reason="started";
  Mac mac;
  if (mach_timebase_info(&mac.timebase)!=KERN_SUCCESS||!mac.timebase.numer||!mac.timebase.denom) { fprintf(stderr,"Mach timebase unavailable\n");free(s->records);free(s);return 2; }
  s->numer=mac.timebase.numer;s->denom=mac.timebase.denom;
  size_t cpu_size=sizeof(s->logical_cpus);
  if (sysctlbyname("hw.logicalcpu",&s->logical_cpus,&cpu_size,NULL,0)||s->logical_cpus<=0) { fprintf(stderr,"Host CPU count unavailable\n");free(s->records);free(s);return 2; }
  struct utsname info;
  if (uname(&info)) { free(s->records);free(s);return 2; }
  snprintf(s->kernel,sizeof(s->kernel),"%s",info.release);snprintf(s->machine,sizeof(s->machine),"%s",info.machine);
  s->ops=(Ops){mac_now,mac_read,mac_children,mac_host,mac_self,mac_sleep,&mac};
  (void)signal(SIGTERM,stop_signal);(void)signal(SIGINT,stop_signal);
  observe(s);
  /* All file writes happen after observation has stopped. */
  FILE *output=fopen(s->output,"wx");
  bool saved=output&&dump(s,output);
  if (output && fclose(output)) saved=false;
  int result=saved&&s->ok?0:1;
  if (!saved) fprintf(stderr,"HOST_OBSERVER_SAVE_FAILED\n");
  free(s->records);free(s);return result;
}
#elif !defined(MOUSE_HOST_OBSERVER_TEST)
#error This external sampler requires Apple system headers.
#endif
