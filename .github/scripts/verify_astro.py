"""Verify migration completeness before either public deployment is replaced."""
from pathlib import Path
import json
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / 'astro-site'
DIST = APP / 'dist'
GENERATED = APP / 'src/generated'


def html(route):
    path = DIST / route.strip('/') / 'index.html'
    assert path.is_file(), f'Missing output: {route}'
    return BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')


def verify():
    report = json.loads((GENERATED / 'migration.json').read_text(encoding='utf-8'))
    aliases = json.loads((GENERATED / 'aliases.json').read_text(encoding='utf-8'))
    pages = json.loads((GENERATED / 'pages.json').read_text(encoding='utf-8'))
    home = html('/')
    assert home.select_one('meta[name="generator"]')['content'].startswith('Astro'), 'Final renderer must be Astro'
    assert home.find(id='sidebar-open'), 'Missing actual ThoughtLite navigation'
    assert home.find(id='blog-agent-dialog'), 'Missing preserved Agent'
    assert home.find(id='search-dialog'), 'Missing preserved search'
    assert home.find(id='global-music'), 'Missing preserved music player'
    for route in ['/note/', '/learning/', '/jotting/', '/about/', '/projects/', '/links/', '/footprints/', '/sichuan-tibet-318/', '/hainan-island/', '/chengdu-xian/', '/history/', '/listening/']:
        html(route)
    music = json.loads((APP / 'src/data/qq-music.json').read_text(encoding='utf-8'))
    listening = html('/listening/')
    # Compare against the current snapshot, not hard-coded playlist/song counts.
    song_links = listening.select('.songs a')
    playlist_links = listening.select('.playlists a')
    assert [a['href'] for a in song_links] == [
        f"https://y.qq.com/n/ryqq_v2/songDetail/{song['mid']}" for song in music['songs']
    ], 'Listening songs missing, reordered, or linked to the wrong track'
    assert [a['href'] for a in playlist_links] == [
        f"https://y.qq.com/n/ryqq_v2/playlist/{playlist['id']}" for playlist in music['playlists']
    ], 'Listening playlists differ from the snapshot'
    assert listening.select_one('time')['datetime'] == music['syncedAt'], 'Listening snapshot date differs'
    assert music['report']['providedOn'] in listening.select_one('.report-note').get_text(), 'Missing report provenance date'
    for alias in aliases:
        original = '/' + alias['path'] + '/'
        redirect = html(original)
        assert redirect.select_one('link[rel="canonical"]')['href'].endswith(alias['target']), original
        destination = html(alias['target'])
        if alias['path'] not in {'archive', 'essays'}:
            comments = destination.select_one('[data-comment-path]')
            if comments: assert comments['data-comment-path'] == original, f'Comment path changed: {original}'
    for page in pages:
        html(page['path'])
    for asset in ['footprints-data.json', '318-journey-data.json', 'hainan-journey-data.json', 'css/leaflet.css', 'js/blog-agent.js', 'img/avatar.png', 'legacy-scoped.css']:
        assert (DIST / asset).is_file(), f'Missing public asset: {asset}'
    assert (DIST / 'feed.xml').is_file()
    assert (DIST / 'sitemap-index.xml').is_file()
    print(json.dumps({'verified': report, 'renderer': 'Astro + ThoughtLite', 'original_comment_paths': 'preserved'}, ensure_ascii=False))


if __name__ == '__main__':
    verify()
