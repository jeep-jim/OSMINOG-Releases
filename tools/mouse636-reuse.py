#!/usr/bin/env python3
"""Byte-frozen635 reuse with explicit636 identities and reviewed replacement gates.

Historical634/635 validators and receipts are never rewritten. Current636
replaces only deleted tile search, modal Agent settings and closed snapshot
switching; all remaining algorithms keep their native/input/pixel bounds.
"""
import ast
import hashlib
from pathlib import Path
import runpy

FROZEN = {'mouse635-633-owner-evidence.py': '0fc2ee5e7809cf9fae7b86b46db6a19a04434f3272a24bba4ecdce8d91a8ade3', 'mouse635-agent-chat-evidence.py': 'e84ea9f43eea6aa0624d4c8bbd9cbbe0b2e026d8d398d8ed1fe48f2db9fc9af5', 'mouse635-capture-evidence.py': '130afc087f3f0e8fc5912f0d1446b9be04bf57a957fd3569a71cc80b7194e78a', 'mouse635-context-evidence.py': '6347ec72bacfc57bfbf3236fa3b5fbc2ed1995b1d6892e082b7a27383008bfaa', 'mouse635-current.py': '1b19e950997096234ff472151e43146c7ceaf27d7524195087dae7939e548e9d', 'mouse635-download-evidence.py': 'b26d44420be2521f4b74fbcf195d90d1a16e478eae57635f2275c5a437cebe47', 'mouse635-evidence.py': '27a8da89bdd5314466e4981751ac62cda5256e872b77dd00e2a774bbc5960e23', 'mouse635-feedback-evidence.py': 'eb97cd13b88e1e90a693d9ff0ca470bec9ca9cb7b762088c624cb73f53ec6a9f', 'mouse635-focused-evidence.py': '18cd810f7bfec2a2b1bb763309ef477ad60cf975a3f205f64471c0b956bdaa7a', 'mouse635-library-evidence.py': '8e54690e48746c680f1e16d6784dacc49bdb1f133a2a16a803301f6fc728d6e3', 'mouse635-linux-evidence.py': '30e97a0417f2a5a521f20fa72ae9eae7f8a6446499c8c77bd9a2c04fbc67c178', 'mouse635-linux-release.py': 'b38cf90e74f420e152a82f5f2abc94672c64df6a1ccde2a1e65caee6f5667054', 'mouse635-native-evidence.py': '79cbd8bf2d1774cc2b5b7076c0c32d8b9fda793c720e865a5c53dbf66364d6dc', 'mouse635-owner-feedback-evidence.py': 'c8f7686941fe709a62c7ef665ec98b22b71d7bb58036394dc4deff8f8f5f3afb', 'mouse635-pane-layout-evidence.py': '951c22baa677075444c5b80387b40e05b96410bd7cd49aac92416273584d8ca4', 'mouse635-public-search-evidence.py': 'bbe2f6a0460a5f3d8a333f686dc5e3655ffb31cc076597c579f133247d0216f2', 'mouse635-publish-plan.py': 'f45937aef4ee756901489990d153a7185423231668b0d17112fa5f7fdc70654d', 'mouse635-release.py': 'df454c47b4afd43626069745deb77f8bdce690d4e4a04d41141d3fa39d5c845d', 'mouse635-retained-native-evidence.py': 'a52ea3260566103972d8402ca105f32e9219c6be13e3588249f2d9dfa75a5949', 'mouse635-retained-owner-evidence.py': '22528ca013237ea4950e0240e800e2349a994c19764db797067b2604009b3728', 'mouse635-reuse.py': 'b20717bb29488b2061a4469728055e3669c7369af12a3b2d6f40008c9d253193', 'mouse635-search-evidence.py': '1e66d73a17f1978841360cd6b170958db568d2ad741125462d9bd7e6f5e71a40', 'mouse635-task-evidence.py': '8071da5a72c840f762daa43ee0edca6fc484ed4ba83c16d960025018839d19bb', 'mouse635-ui-evidence.py': '2af4df737d176ae0f1758fcf7208f52b8922428a750fe51fc5a9d80f3c3a243d', 'mouse635-upgrade-evidence.py': '6d0e10e417714e941840ab6f7342a25115502c085b4fa255849feb7841a9124f', 'mouse635-windows-release.py': 'ced48b6b7441d4367cc167ecb40c63acf136dc6bd18fa7866c7c040a36f61895', 'mouse635-workspace-evidence.py': '128b3a232246687e3e806900f629d7932f73482a9a452109ad97173355b24b03', 'test-mouse635-evidence.py': 'cc495fd1db27740f7de7304ff278d49506f16990394cc6232d4a1d9469fae5a9', 'test-mouse635-ui-evidence.py': '8ba744b6ecf77e2b5db823f8706011b1c19fd820a4c4e5108bbda4662f393da9', 'test_mouse635_633_owner_evidence.py': '656e48122f4759a53d3aba892464d95e44e0eedf4a61b568fb4aee7a105c77cf', 'test_mouse635_agent_chat_evidence.py': '9a9af2185d8ba43e97e13908b4b89a158386e7e8c53e16daee4c18f72496c6a2', 'test_mouse635_context_evidence.py': '89b0a9b47bb224060963b70ee722a523bdd21fd420a60a2fada4e6521a19fbdc', 'test_mouse635_feedback_evidence.py': 'c1c4aa0cbcd1164ff4bce5aadd58d51ccd702dc5b983ba1d2eaaeed25a7d92c4', 'test_mouse635_library_evidence.py': 'c29ff0c06fa41edd208681f7960d898e1057871c6ede11396c134fea8731407e', 'test_mouse635_linux_evidence.py': 'ab5c607647a23e6d29682e9af926b76be3687e68a516a4612199ac42b36d4960', 'test_mouse635_linux_release.py': '78349b3a71565900d5f81347859e99e6ab70031fac94694f42f3b8852ec109a3', 'test_mouse635_native_report.py': 'd86b5cf521c6418a1e974b32b9a597ac14cda6cf46316b913b8b3b7a1f618be4', 'test_mouse635_owner_feedback_evidence.py': 'cea5dba4c07cb8a847696fbbc2bdfc02a2a3dcc5a299fd7b5deb22f7d07aaf5a', 'test_mouse635_pane_layout_evidence.py': 'f36621f28b16d2bcbebb6b2fe3e2ebedacd1d2d5f2749f0208689a57d8c9efe7', 'test_mouse635_public_search_evidence.py': 'ff2cfd3c5b5e8dd4bc434a7930497f3377099e224cb5114e0e4e8cd0ab75e777', 'test_mouse635_publish_plan.py': '4bad4977a7346b0ffa4b96c686e3338c8675fed0c351bad5919a897a2f2d6a72', 'test_mouse635_release_bytes.py': '0469f45f95ff0a6ddf11229f5e29b48f86b286d2beb51081bbe7025bed35699f', 'test_mouse635_retained_owner_evidence.py': '23802238ec18b7b43f4acb55c4ff442828dd70298ad7e1f02b5eea0d71930fd9', 'test_mouse635_reuse.py': 'ca8a5a743a4d70e8c92fe4d9c9f0059919987e9b3217123dc07a5c0ffe5254d5', 'test_mouse635_search_evidence.py': '4e7668c5e88ff033ae9f5036f84cab0499762bffc9a00a466463e1f784574642', 'test_mouse635_task_evidence.py': '58ad6e5d913fab6ed5f0a86d2cfa98495f1566325e7fcc7b61d04b46f576a695', 'test_mouse635_upgrade_evidence.py': '23a5fd52015211e9b11f3bc5273773fa71b477d19e2bae617944e26769628893', 'test_mouse635_windows_release.py': 'b4827dd60c1d841878792bfff0fe763cc9019d47fe6798b25d971beeee02f92c', 'test_mouse635_workspace_evidence.py': '27191fe7f5732caafbe5c8f60d5825e02abd94acd6eae7926af36cd6238e1870'}
MODULES = {name: name.replace('mouse635-', 'mouse636-').replace('test_mouse635_', 'test_mouse636_') for name in FROZEN}


def checked(name):
    if name not in FROZEN:
        raise ValueError('Unreviewed636 dependency: ' + name)
    raw = Path(__file__).with_name(name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN[name]:
        raise ValueError('Immutable636 dependency changed: ' + name)
    return raw


def legacy():
    checked('mouse635-reuse.py')
    return runpy.run_path(str(Path(__file__).with_name('mouse635-reuse.py')))


def target(name):
    if name in MODULES:
        return MODULES[name]
    previous = legacy()['target'](name)
    if previous not in MODULES:
        raise ValueError('Unreviewed636 dependency: ' + name)
    return MODULES[previous]


def adapted_tree(name, *, current_native=False):
    if name in FROZEN:
        tree = ast.parse(checked(name), filename=str(Path(__file__).with_name(name)))
    else:
        tree = legacy()['adapted_tree'](name, current_native=current_native)

    class Identity(ast.NodeTransformer):
        def visit_Constant(self, node):
            if not isinstance(node.value, str):
                return node
            value = node.value.replace('6.0.35', '6.0.36').replace('MOUSE635_', 'MOUSE636_').replace('publish-mouse635', 'publish-mouse636')
            for old, new in MODULES.items():
                value = value.replace(old, new)
            for old, new in [
                ('mouse635-windows-release', 'mouse636-windows-release'),
                ('mouse635-linux-release', 'mouse636-linux-release'),
                ('mouse635-release', 'mouse636-release'),
                ('mouse-635-upgrade', 'mouse-636-upgrade'),
                ('mouse-635-profile-upgrade', 'mouse-636-profile-upgrade'),
                ('mouse-635-owner-feedback', 'mouse-636-owner-feedback'),
                ('mouse-634-owner-feedback', 'mouse-636-retained-owner-feedback'),
                ('ownerFeedback634', 'ownerRetained636'),
                ('MOUSE_621_SMOOTH_DESKTOP_NATIVE_SLIDE_PASS', 'MOUSE_636_LIVE_DESKTOP_TRANSITION_PASS'),
                ('smooth-native-desktop-slide', 'live-desktop-switch-performance'),
                ('MOUSE_635_OWNER_FEEDBACK_PASS', 'MOUSE_636_OWNER_FEEDBACK_PASS'),
                ('MOUSE_635_REAL_629_TO_635_REPLACE_RELAUNCH_PROFILE_PASS', 'MOUSE_636_REAL_629_TO_636_REPLACE_RELAUNCH_PROFILE_PASS'),
                ('MOUSE_635_WINDOWS_REAL_629_TO_635_PROFILE_PASS', 'MOUSE_636_WINDOWS_REAL_629_TO_636_PROFILE_PASS'),
                ('MOUSE_635_UPGRADE_PROFILE_', 'MOUSE_636_UPGRADE_PROFILE_'),
                ('real-634-to-635-profile-preserving-replacement', 'real-published-predecessor-to-636-profile-preserving-replacement'),
                ('real-629-to-635-profile-preserving-install', 'real-629-to-636-profile-preserving-install'),
            ]:
                value = value.replace(old, new)
            # Shared retained635 library/pane PNG names remain actual filenames.
            if current_native and node.value == r'mouse-635-[a-z0-9-]+\.png':
                value = r'mouse-(?:635|636)-[a-z0-9-]+\.png'
            if node.value == r'mouse-(?:634-|635-search-)[a-z0-9-]+\.png':
                value = r'mouse-(?:634|636)-[a-z0-9-]+\.png'
            return ast.copy_location(ast.Constant(value=value), node) if value != node.value else node

    return ast.fix_missing_locations(Identity().visit(tree))


def load(name, *, namespace=None, current_native=False):
    scope = namespace if namespace is not None else {}
    original = scope.get('__name__')
    scope['__file__'] = str(Path(__file__).with_name('mouse636-native-evidence.py' if current_native else target(name)))
    scope['__name__'] = 'retained636_' + name.replace('-', '_')
    try:
        exec(compile(adapted_tree(name, current_native=current_native), scope['__file__'], 'exec'), scope)
    finally:
        if original is not None:
            scope['__name__'] = original
    return scope
