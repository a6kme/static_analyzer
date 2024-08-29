## one static Analyzer to rule them all
### System requirements
1. Docker runtime
1. python3

### How to run
1. Clone the repo `git clone https://github.com/a6kme/static_analyzer`
1. Install the dependencies `pip install -r api/requirements.txt'
1. Run the analyzer
```
from api.src.analyzer import StaticAnalyzer
from api.src.config import AppConfig
from api.src.models import GithubRepo
from api.src.services import GithubService

config = AppConfig.get_config()
repo = GithubRepo(name='pygoat', owner='adeyosemanputra')
pr = GithubService(config).get_pull_request(repo, 11)
StaticAnalyzer(config).static_review(pr)
for file in pr.files:
    print(file.review)
```

### RoadMap
1. Add other languages
1. Publish as a python library (If required)
