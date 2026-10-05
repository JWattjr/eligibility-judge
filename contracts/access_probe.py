# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import json
from genlayer import *

class EligibilityAccessProbe(gl.Contract):
    results: TreeMap[str, str]

    def __init__(self):
        pass

    @gl.public.write
    def probe(self, url: str) -> None:
        def fetch():
            response = gl.nondet.web.get(url)
            return {'status': response.status, 'reachable': response.status == 200}
        self.results[url] = json.dumps(gl.eq_principle.strict_eq(fetch))

    @gl.public.view
    def result(self, url: str) -> str:
        return self.results.get(url, '')
