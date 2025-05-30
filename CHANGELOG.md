# Changelog

## [0.1.0] - 2025-05-30
### Changes:

#### 🚀  Features

- *(changelog)* Add release.sh script - ([42a651e](https://github.com/mapswipe/mapswipe-backend/commit/42a651eb0c46183df614079299401998bbbab352))
- *(changelog)* Add config for git cliff - ([fcd63fe](https://github.com/mapswipe/mapswipe-backend/commit/fcd63fe3a15546faf0b1c5346b59a2acfb69a8a6))
- *(ci)* Add workflow for github release from tag - ([2024203](https://github.com/mapswipe/mapswipe-backend/commit/2024203fd25da1db39f06435fdc612d036e481bf))
- *(community-dashboard)* Migrate from existing system - ([7e304c8](https://github.com/mapswipe/mapswipe-backend/commit/7e304c86212dcb3437bc206efd6506835480933a))
- *(docker-compose)* Add option to override env file - ([ed07465](https://github.com/mapswipe/mapswipe-backend/commit/ed07465aaabe1dadb74bd734d509f6d23a0e9a3b))
- *(health-check)* Add custom metadata in json response - ([5f738ba](https://github.com/mapswipe/mapswipe-backend/commit/5f738ba7250816d0df15ecddf0897be4ebbbb75e))
- *(health-check)* Add ensure_csrf_cookie with health-check - ([b367568](https://github.com/mapswipe/mapswipe-backend/commit/b36756872a3015844d1082053a7e0fb66f61bab4))
- *(pre-commit)* Add gitleaks - ([7f5ccaa](https://github.com/mapswipe/mapswipe-backend/commit/7f5ccaa2c10f14d9312a13b9987ffad2615f29f9))
- *(sentry)* Add sentry config override for celery beat tasks - ([1660f20](https://github.com/mapswipe/mapswipe-backend/commit/1660f2057a97c8fe2a0f28d516dd7aec4ba74a64))

#### 🐛 Bug Fixes

- *(ProjectAssetType)* Add file field - ([47a9859](https://github.com/mapswipe/mapswipe-backend/commit/47a985934cbc97fd372e94828f2043d1d70a6ecc))
- *(celery)* Fix crontab value issue - ([1366fa3](https://github.com/mapswipe/mapswipe-backend/commit/1366fa3dd317de35e8f63d3598f1ce297040355b))
- *(celery-beats)* Fix and add django check for beats task validation - ([0ef82c1](https://github.com/mapswipe/mapswipe-backend/commit/0ef82c1a8feae208cd59e6de35c83066af856ce2))
- *(csrf)* Add missing CSRF trusted origin - ([bb67a74](https://github.com/mapswipe/mapswipe-backend/commit/bb67a74201fe07ddd6dab984092e3a4f45443794))
- *(enums)* Add tutorial icon enum to the list - ([5f2477a](https://github.com/mapswipe/mapswipe-backend/commit/5f2477a898eed1e78d611ce1e05983690d133134))
- *(graphql)* Add custom file type to fix url issue - ([920233e](https://github.com/mapswipe/mapswipe-backend/commit/920233e77a6be116874c65d97e8f6fd78ef22ed0))
- *(graphql)* Disable graphiql in graphql/ endpoint - ([771ab75](https://github.com/mapswipe/mapswipe-backend/commit/771ab753580aec60faebfe5f65b22a7733ee1aba))
- *(heath-check)* Remove 'files' field from GitHub API response - ([1edf0f3](https://github.com/mapswipe/mapswipe-backend/commit/1edf0f36fba5bdac6a5977d5fa8cd42003e95bcc))
- *(helm)* Add missing configurations - ([bd6b285](https://github.com/mapswipe/mapswipe-backend/commit/bd6b2854e8ecc09f1b4f503b583fa8f0d10e1d10))
- *(sentry)* Fix site tag validation error - ([55df806](https://github.com/mapswipe/mapswipe-backend/commit/55df806d23105c4d1b7ca8f661bf015e28152394))
- *(tile_server)* Update quadKey with quad_key - ([d1b068b](https://github.com/mapswipe/mapswipe-backend/commit/d1b068be5f19a7bc560c4f53badd12019bbc66e6))
- *(tutorial)* Use enum for conditional checks - ([463ec63](https://github.com/mapswipe/mapswipe-backend/commit/463ec63a43ca3b04de4d7c9a239e1149b82c49c2))
- *(typing)* Ignore typing errors for custom logics - ([b14c3aa](https://github.com/mapswipe/mapswipe-backend/commit/b14c3aab98fea0c29890281d8523a295e498615e))
- *(typos)* Fix existing typos - ([4edc498](https://github.com/mapswipe/mapswipe-backend/commit/4edc498594a881762596c11775b96fcd37af6e06))

#### 📚 Documentation

- *(changelog)* Add git-cliff docs - ([98b3f54](https://github.com/mapswipe/mapswipe-backend/commit/98b3f5438279a208112015292e3c4b52de404d69))

#### ⚙️ Miscellaneous Tasks

- *(dependencies)* Add missing s3 dependencies boto3 - ([075786e](https://github.com/mapswipe/mapswipe-backend/commit/075786ec9886bf198b4fc1dc49cc29c8b94435c7))
- *(helm)* Upgrade django-app chart to 0.1.1 - ([36074b5](https://github.com/mapswipe/mapswipe-backend/commit/36074b59396cdf371cb251a8d04e4a6a369a7622))
- *(helm)* Replace `alpha` helm/docker name with `dev` - ([734007e](https://github.com/mapswipe/mapswipe-backend/commit/734007e06665dbb2bed595003cc9acf25f63f167))
- *(helm)* Rename values-test.yaml to linter_values.yaml - ([1ff9a68](https://github.com/mapswipe/mapswipe-backend/commit/1ff9a68db2e8664f7dadd34e806b8a20bca41089))
- *(release)* Generate initial changelog - ([f600dd8](https://github.com/mapswipe/mapswipe-backend/commit/f600dd82dbde41450a6df4b43f5c24b62f26ac1c))

#### Pre-commit

- *(typos)* Ignore changelog file - ([7291757](https://github.com/mapswipe/mapswipe-backend/commit/729175710be0a1a7ecb2107659a0a7bfae4812b3))
- *(typos)* Add typos hook - ([9d30be4](https://github.com/mapswipe/mapswipe-backend/commit/9d30be4c32f860332a839450335694c7072b1577))

### 🍻 Pull Requests (13)
- (#1) [Feature/setup](https://github.com/mapswipe/mapswipe-backend/pull/1)
- (#6) [Feature/core models](https://github.com/mapswipe/mapswipe-backend/pull/6)
- (#12) [Update configuration for pyright](https://github.com/mapswipe/mapswipe-backend/pull/12)
- (#13) [Add authors on todo and fixme comments](https://github.com/mapswipe/mapswipe-backend/pull/13)
- (#14) [Create a geojson processed file](https://github.com/mapswipe/mapswipe-backend/pull/14)
- (#15) [Support dynamic no. of assets to support multiple project types](https://github.com/mapswipe/mapswipe-backend/pull/15)
- (#19) [Use project asset for project image uploads](https://github.com/mapswipe/mapswipe-backend/pull/19)
- (#23) [Feature/assets deletion manager](https://github.com/mapswipe/mapswipe-backend/pull/23)
- (#24) [Organization related queries](https://github.com/mapswipe/mapswipe-backend/pull/24)
- (#25) [Feature/tutorial mutations](https://github.com/mapswipe/mapswipe-backend/pull/25)
- (#29) [Feature/community dashboard](https://github.com/mapswipe/mapswipe-backend/pull/29)
- (#30) [Feat/helm update](https://github.com/mapswipe/mapswipe-backend/pull/30)
- (#36) [Feat/changelogs](https://github.com/mapswipe/mapswipe-backend/pull/36)

### :tada: New Contributors (2)

- [@tnagorra](https://github.com/tnagorra) made their first contribution in [#36](https://github.com/mapswipe/mapswipe-backend/pull/36)
- [@frozenhelium](https://github.com/frozenhelium) made their first contribution

<!-- generated by git-cliff -->
