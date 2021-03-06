regex = {
    'm3u-fmt': r'(mpegurl)|(m3u8?)|(octet-stream)',
    'zip-fmt': r'zip|download',
    'html-fmt': r'html|text',
    'stream-fmt': r'video|stream',
    'identity': r'(.+)(www\.)(.+)',
    'port': r'(.+?)(:\d{1,10})(.+)?',
    'top': r'(.+)\.((?:.(?!\.))+)$',
    'short': r'(ift\.tt)|(bit\.(ly)|(bit\.do\/))|(bc\.vc)|(goo\.gl)|(link\.tl)',
    'ip': r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$',
    'm3u': r'(\.m3u8?)|(&?type=m3u8?)',
    'streams': r'(\.ts)|(\.mp4)|(\.mkv)|(\.ch)|(\.mpg)|(\/mpegts)',
    'dl': r'(=download)|(dl=)|(\/playlist)$|(\/playlist\/)|(rndad=)|(\.php)|(download-attachment)',
    'ndl': r'(\/playlist\/page)|(tag\/playlist\/)',
    'zip': r'(\.zip)|(&?type=zip)',
    'raw': r'(pastebin\.com\/raw\/.{8})$',
    'invalid': r'(#)|(javascript:(%\d+)?void\(0\))|(^\/$)|(\.png)|(\.jpeg)|(^$)',
    'ext': r'^#(EXT)|(MY)',
    'whitespace': r'^\s*$',
    'digits': r'^\d*$',
    'params': r'(.+?)(\??&.+)',
    'end': r'(.+)\/$',
    'ignore': r'(\.mp3)|(\.aac)|(archive\.org)',
    'pure': r'^[\w\d]+$',
    'phrases': r'[\w\d]+',
    'metacharacters': r'^[\w\d]',
    'max-results': r'(\??&?max-results=[\d]+)',
    'by-date': r'(\??&?by-date=(true|false))',
    'start': r'(\??&?start=[\d]+)',
    'updated-max': r'(\??&?updated-max=[^&]+)',
    'lost-password': r'(\??&?action=lostpassword&redirect_to[^&]+)&?',
    'title': r'#EXTINF:-?[\d\.]+(.*), ?(.*[:\|-])? ?(.+)'
}
def get():
    return regex
