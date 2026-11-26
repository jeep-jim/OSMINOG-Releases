"""Explicitly synthetic641 contracts for retained mutation tests, not CI proof."""
import copy


def link_route(chat, selector, url, grid, ident='new-link', pid=11):
    pointer = {'type': 'pointerdown', 'id': selector[1:], 'href': url, 'matches': True,
               'trusted': True, 'isTrusted': True, 'button': 0, 'pointerType': 'mouse', 'at': 102}
    click = {'selector': selector, 'source': 'XTest', 'action': 'intercepted-link', 'pid': pid, 'at': 100,
             'evidence': 'Trusted pointerdown on the exact anchor before isolated click interception',
             'point': {'x': 40, 'y': 50}, 'tabId': chat['id'], 'webContentsId': chat['webContentsId'], 'events': [pointer]}
    back = {'selector': '#return-to-grid', 'source': 'XTest', 'pid': pid, 'at': 200,
            'point': {'x': 60, 'y': 50}, 'events': [{'type': 'click', 'trusted': True, 'matches': True}], 'navigates': False}
    return {'source': 'Synthetic fixture only', 'selector': selector, 'url': url,
            'beforeGrid': copy.deepcopy(grid), 'returnedGrid': copy.deepcopy(grid),
            'state': {**copy.deepcopy(grid), 'classicTabId': ident, 'view': 'classic',
                      'panes': [{'id': 'p0', 'view': 'classic'}], 'returnVisible': True},
            'tab': {'id': ident, 'webContentsId': chat['webContentsId'] + 100, 'url': url, 'lane': 'main', 'previewOf': ''},
            'chatBefore': copy.deepcopy(chat), 'chatAfter': {**copy.deepcopy(chat), 'ticks': chat['ticks'] + 1},
            'input': click, 'returnInput': back}


def preview(report, owners, inputs):
    """Only new link/setup semantics change; all retained native mutations stay."""
    report['source'] = 'Native cross-origin link routing, explicit existing-preview fixture, native resize and native chooser/header transfers'
    chat = report['chatBefore']; url = report['origins']['preview'] + '/page/3/'
    grid = {'classicTabId': '', 'view': 'grid', 'tree': {'type': 'split', 'axis': 'x'},
            'slots': copy.deepcopy(report['initial']['slots']), 'aiId': chat['id'], 'previewId': '',
            'panes': [{'id': 'p1', 'view': 'grid'}, {'id': 'p2', 'view': 'grid'}], 'returnVisible': False}
    route = link_route(chat, '#ai-preview-link', url, grid)
    report['linkRouting'] = [route]; report['nativeLinkClick'] = route['input']['events'][0]
    inputs[:] = [row for row in inputs if row.get('selector') != '#ai-preview-link']
    inputs[:0] = [route['input'], route['returnInput']]
    source = 'Explicit fixture setup for existing lower-pane resize and transfer controls; not a native-link outcome'
    def setup(ident):
        return {'source': source, 'action': 'browser.command(open)', 'url': url, 'lane': 'side', 'previewOf': chat['id'], 'id': ident}
    report['open'] = {'input': setup(report['initial']['previewId'])}
    report['headerMove']['open'] = setup(report['headerMove']['before']['id'])
    return report, owners, inputs
