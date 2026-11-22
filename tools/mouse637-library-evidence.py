#!/usr/bin/env python3
"""Retain library stability gates with the exact637 content preview geometry."""
import runpy
from pathlib import Path
_reuse=runpy.run_path(str(Path(__file__).with_name("mouse637-reuse.py")))
_reuse["load"]('mouse636-library-evidence.py',namespace=globals())


def _placeholder_size(row,view):
 # library-view.css: 18px selection column, 7px gap, 108px image height.
 # mouse-620.css adds 6px horizontal/9px vertical padding; mouse-628.css
 # removes borders. Width follows the actual row, not one runner viewport.
 image,box=row['image'],row['row']
 if view=='grid': return abs(image['height']-112)<=1
 if view!='list': return False
 return all(abs(actual-expected)<=1 for actual,expected in (
  (image['x'],box['x']+6),(image['y'],box['y']+9),
  (image['width'],box['width']-37),(image['height'],108),(box['height'],126)))


def placeholder_geometry(receipt,view,copies):
 need(isinstance(receipt,dict) and receipt.get('controlledDelay') is True,'actual delayed preview geometry missing')
 before,after=receipt.get('before',{}),receipt.get('after',{})
 need(all(isinstance(row,dict) and row.get('kind')=='captures' and row.get('view')==view for row in (before,after)),'placeholder geometry belongs to another library mode')
 need(all(finite(row.get('scrollTop')) and row['scrollTop']>=0 for row in (before,after)) and abs(after['scrollTop']-before['scrollTop'])<=1,'preview completion moved the list scroll')
 old,new=before.get('rows'),after.get('rows')
 need(isinstance(old,list) and isinstance(new,list) and len(old)==len(new)==14 and all(isinstance(row,dict) for row in old+new),'all fourteen image rows need raw placeholder geometry')
 need([row.get('id') for row in old]==copies[:14] and [row.get('id') for row in new]==copies[:14],'placeholder rows were replaced, reordered or omitted')
 delayed=ordered_ids(receipt.get('delayedIds'),'controlled delayed image identities missing')
 need(set(delayed)<=set(copies[:14]) and copies[8] in delayed,'viewed owned capture was not held before its preview')
 sequences=receipt.get('requestSequences')
 need(isinstance(sequences,list) and len(sequences)==len(delayed) and all(type(value) is int and value>0 for value in sequences) and len(set(sequences))==len(sequences),'delayed preview request sequence binding missing')
 for left,right in zip(old,new):
  for name in ('row','image','checkbox'):
   a,b=left.get(name,{}),right.get(name,{})
   need(isinstance(a,dict) and isinstance(b,dict) and all(finite(box.get(key)) for box in (a,b) for key in ('x','y','width','height')) and all(box['width']>0 and box['height']>0 for box in (a,b)),'placeholder controls have missing or empty bounds')
   need(all(abs(b[key]-a[key])<=1 for key in ('x','y','width','height')),'preview completion moved a row, image or checkbox')
  need(_placeholder_size(left,view),'preview did not reserve its actual list/grid dimensions')
  need(all(type(row.get(key)) is bool for row in (left,right) for key in ('thumbnail','decoded')),'placeholder image state missing')
  if left['id'] in delayed: need(left['thumbnail'] is False and right['thumbnail'] is True and right['decoded'] is True,'held placeholder did not become a real decoded preview')
 return list(zip(sequences,delayed))
