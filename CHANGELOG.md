# Changelog

## [0.2.0-dev7](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.0-dev6..v0.2.0-dev7) - 2025-09-04
### Changes:

#### 🚀  Features

- *(docker)* Set MAPILLARY_API_KEY key on docker compose - ([f4a04b3](https://github.com/mapswipe/mapswipe-backend/commit/f4a04b35c82590911de2cdf1cc1aef02708c27d0))
- *(project)* Update mapillary api calls - ([5620d2a](https://github.com/mapswipe/mapswipe-backend/commit/5620d2a9e8c9e3b6c63c3f0c6bdb71c1b70c2831))
- *(project)* Add street project type - ([d149800](https://github.com/mapswipe/mapswipe-backend/commit/d149800573669fb717f4f4b32a92004737c475b5))
- *(street)* Add max time spend percentile - ([a48328d](https://github.com/mapswipe/mapswipe-backend/commit/a48328d6036c042fbb5439d3c1dc6aa5e86d15aa))
- *(street)* Add numberOfGroups for the street project - ([a274ca1](https://github.com/mapswipe/mapswipe-backend/commit/a274ca11d9458bfbdfe49d89f042c00d59e1fc91))
- *(street)* Add tutorial schema for street - ([6836bf6](https://github.com/mapswipe/mapswipe-backend/commit/6836bf68ff8041de01599cd367929fe1523158c7))
- *(street)* Tasks and groups for street project - ([8e04cf5](https://github.com/mapswipe/mapswipe-backend/commit/8e04cf5487571ed044bef84b20766c380a035513))
- Use pre-parsed project names in loaddata - ([2720a07](https://github.com/mapswipe/mapswipe-backend/commit/2720a075e4bdec32fae4da18ac859fa34a835fdb))

#### ⚙️ Miscellaneous Tasks

- *(migration)* Merge migrations - ([08a0734](https://github.com/mapswipe/mapswipe-backend/commit/08a0734f6d4d95757e13df83889c4decf171937e))

### 🍻 Pull Requests (2)
- (#118) [Feature: Street project type](https://github.com/mapswipe/mapswipe-backend/pull/118)
- (#147) [Feat: use pre-parsed project names in loaddata](https://github.com/mapswipe/mapswipe-backend/pull/147)


## [0.2.0-dev6](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.0-dev5..v0.2.0-dev6) - 2025-09-03
### Changes:

#### 🚀  Features

- *(admin)* Make django form selection lazy - ([162e21f](https://github.com/mapswipe/mapswipe-backend/commit/162e21fbdef5bb4934dcaeac5fc317a588d63239))
- *(asset)* Add validation for asset_specifics - ([0fb7b2b](https://github.com/mapswipe/mapswipe-backend/commit/0fb7b2bf1d62299e9e0aa44ffd354854579f8ded))
- *(graphql)* Add contributor user in user type - ([40f8481](https://github.com/mapswipe/mapswipe-backend/commit/40f84810d2c70cc091134f38ccd9778df3c7cf8e))
- *(project)* Add link to project in mapswipe website - ([8df3d8c](https://github.com/mapswipe/mapswipe-backend/commit/8df3d8c9fa47d944a6ef5cfecb24133e9d8ed349))
- *(tutorial)* Make hint and success information mandatory on scenarios - ([ea59d9b](https://github.com/mapswipe/mapswipe-backend/commit/ea59d9bb695429ea5ba6d3a6f36bb3729dd31c9c))
- *(user)* Add contributor user on user query - ([ea12812](https://github.com/mapswipe/mapswipe-backend/commit/ea1281232593e5494221e18da53822d4d73e8e9c))

#### 🐛 Bug Fixes

- *(export)* Use first part of the key to get projects for export - ([57c1389](https://github.com/mapswipe/mapswipe-backend/commit/57c138993ce50c39d6c967582fdc1eb3ccad8000))
- *(file)* Set filename max length to 255 - ([0c660a1](https://github.com/mapswipe/mapswipe-backend/commit/0c660a139ff97e6c573b9ea7484ca333005fefd9))
- *(test)* Update field level error checks on project - ([def1741](https://github.com/mapswipe/mapswipe-backend/commit/def1741263d3af10ee6218443b7aba76115627fe))
- *(user)* Add anonymizedEmail to usertype - ([b68092c](https://github.com/mapswipe/mapswipe-backend/commit/b68092c9a77697462994385e63260eb3462d510c))
- *(user)* Rename anonymize_email to anonymized_email - ([f2f7460](https://github.com/mapswipe/mapswipe-backend/commit/f2f74609db5cf000f08d65d82f04ea0eddbeb57c))
- *(usergroup)* Fix syncing issue on user group and user group membership timestamp - ([1230e34](https://github.com/mapswipe/mapswipe-backend/commit/1230e34cf47090ba0959ad328974edeaa08444bc))
- Pytest reportMissingImports - ([0566d2c](https://github.com/mapswipe/mapswipe-backend/commit/0566d2c7031719b9149030bb303d8ead2696e3c8))

#### 🚜 Refactor

- *(serializer)* Return field level validation errors where possible - ([db5db76](https://github.com/mapswipe/mapswipe-backend/commit/db5db769d5126ed9554d09210147572379132e75))
- *(tutorial)* Use field level validation for tutorial status mutation - ([93077e1](https://github.com/mapswipe/mapswipe-backend/commit/93077e1a01f60e9f7c30cecd97fa3266e4024f56))

#### ⚙️ Miscellaneous Tasks

- *(main)* Fix typos - ([5e5d3e9](https://github.com/mapswipe/mapswipe-backend/commit/5e5d3e948e12e320f2afb160f89031646089a760))
- *(migration)* Merge migrations - ([902b82b](https://github.com/mapswipe/mapswipe-backend/commit/902b82bebe5876e2450a2b17508a2ed9080eaf89))
- *(migration)* Use cte_objects instead of default objects - ([0829d7c](https://github.com/mapswipe/mapswipe-backend/commit/0829d7c073b5b6f928b92dbd60e49679702b3ebb))
- *(project)* Cleanup none keys for JSON field for group and task - ([8fefc64](https://github.com/mapswipe/mapswipe-backend/commit/8fefc644e5c77f84035afee8606e4912f98c2c30))
- *(schema)* Add firebase_id in queries - ([6dcb5a6](https://github.com/mapswipe/mapswipe-backend/commit/6dcb5a6774ab8876058a55d7b3cba6de7b81cf87))

### 🍻 Pull Requests (9)
- (#137) [Add link to project in mapswipe website (query)](https://github.com/mapswipe/mapswipe-backend/pull/137)
- (#138) [Set filename max length to 255](https://github.com/mapswipe/mapswipe-backend/pull/138)
- (#139) [Add contributor user on user query](https://github.com/mapswipe/mapswipe-backend/pull/139)
- (#140) [Fix sync issue with usergroup membership and project exports](https://github.com/mapswipe/mapswipe-backend/pull/140)
- (#141) [Feat(admin): make django form selection lazy](https://github.com/mapswipe/mapswipe-backend/pull/141)
- (#142) [Make hint and success information mandatory on scenarios](https://github.com/mapswipe/mapswipe-backend/pull/142)
- (#143) [Add validation for asset_specifics](https://github.com/mapswipe/mapswipe-backend/pull/143)
- (#144) [Feat(graphql): add contributor user in user type](https://github.com/mapswipe/mapswipe-backend/pull/144)
- (#145) [Return field level validation on serializers where possible](https://github.com/mapswipe/mapswipe-backend/pull/145)


## [0.2.0-dev5](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.0-dev4..v0.2.0-dev5) - 2025-09-01
### Changes:

#### 🚀  Features

- *(cron)* Add cron to get user group membership data - ([d27fbd3](https://github.com/mapswipe/mapswipe-backend/commit/d27fbd35991cb3fe520dce104aed87c4dcfb74ba))

#### 🐛 Bug Fixes

- *(cron)* Fix task name for firebase user pull - ([1846a0e](https://github.com/mapswipe/mapswipe-backend/commit/1846a0ec777cb738bc917ee9ffda540cbd86aaef))

### 🍻 Pull Requests (1)
- (#136) [Fix task name for firebase user pull](https://github.com/mapswipe/mapswipe-backend/pull/136)


## [0.2.0-dev4](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.0-dev3..v0.2.0-dev4) - 2025-09-01
### Changes:

#### 🚀  Features

- *(firebase)* Pull user group membership data from firebase - ([9e0d748](https://github.com/mapswipe/mapswipe-backend/commit/9e0d748f645917891ac816cdc32b00db958fdc2c))

#### 🐛 Bug Fixes

- *(firebase)* Use updated schema for user - ([f98abc2](https://github.com/mapswipe/mapswipe-backend/commit/f98abc275ba6b38b93684e6b98751875bb6afa33))
- *(firebase)* Update usergroup archived at value before syncing to firebase - ([7b0404a](https://github.com/mapswipe/mapswipe-backend/commit/7b0404a0158a661f3dd3fae30cc0d14a548cc2ac))

#### 🚜 Refactor

- *(firebase)* Move firebase pull/push logic inside firebase dir - ([fcdf4f4](https://github.com/mapswipe/mapswipe-backend/commit/fcdf4f4b90fbf34ae1215b98066e045576f3a041))

#### 🧪 Testing

- *(firebase)* Add test for user data pull from firebase - ([6972d1e](https://github.com/mapswipe/mapswipe-backend/commit/6972d1efb3e3de571532d0a18fb363e556c324cc))

#### ⚙️ Miscellaneous Tasks

- *(firebase)* Update verbose log on get_list_of_items_from_firebase - ([cb13c13](https://github.com/mapswipe/mapswipe-backend/commit/cb13c1321a1e52968a0ed0c251fd8b0b1484a913))
- *(ruff)* Add docstrings on public class on models - ([9a38b88](https://github.com/mapswipe/mapswipe-backend/commit/9a38b88780d88b2c59035313434519cfb93e27b2))
- *(ruff)* Auto fix issues related to docstrings - ([27b6c65](https://github.com/mapswipe/mapswipe-backend/commit/27b6c6503a10309ec43d6e3ba170130f3245058f))
- *(ruff)* Enable linter for docstrings - ([24e5be4](https://github.com/mapswipe/mapswipe-backend/commit/24e5be4c9c4c7c3a0a7996f7769bf62381b17816))

### 🍻 Pull Requests (3)
- (#132) [Chore(ruff): enable linter for docstrings](https://github.com/mapswipe/mapswipe-backend/pull/132)
- (#133) [Pull user group membership data from firebase](https://github.com/mapswipe/mapswipe-backend/pull/133)
- (#135) [Update usergroup archived at value before syncing to firebase](https://github.com/mapswipe/mapswipe-backend/pull/135)


## [0.2.0-dev3](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.0-dev2..v0.2.0-dev3) - 2025-08-29
### Changes:

#### 🚀  Features

- *(asset)* Add mapswipe-assets as submodule - ([3c33bb8](https://github.com/mapswipe/mapswipe-backend/commit/3c33bb82a0edbe295fd671a635c64dd690d402f8))
- *(cron)* Setup a cron job to fetch users from firebase - ([39d1602](https://github.com/mapswipe/mapswipe-backend/commit/39d1602fd213f8b8896ebe9479fcfe195c628f77))
- *(firebase)* Disable firebase functions on test - ([0c341ce](https://github.com/mapswipe/mapswipe-backend/commit/0c341ce828426aae393fd9c9d2e0cf554a90c859))
- *(lint)* Add a script to bulk ignore warnings - ([ae76e57](https://github.com/mapswipe/mapswipe-backend/commit/ae76e57db8c47ad49a71f8aff0d90b828eaebd7e))
- *(project)* Make project_instruction required on serializer - ([9691c90](https://github.com/mapswipe/mapswipe-backend/commit/9691c9047344223c6ba1f1bb66a9c6283961a804))
- *(project)* Add new field project instruction - ([3d68a0d](https://github.com/mapswipe/mapswipe-backend/commit/3d68a0ddf350babcc1020737a121648b1a69f986))
- *(project)* Add new field project instruction - ([e944a41](https://github.com/mapswipe/mapswipe-backend/commit/e944a411bcb5da24f1863ad3eea62b7a4155d66c))
- *(results)* Process partial data - ([5d8da43](https://github.com/mapswipe/mapswipe-backend/commit/5d8da4364f7ab0adb7275f3f899135bbf98f7c09))
- *(schema)* Monkeypatch graphql printer to sort members alphabetically - ([f14903a](https://github.com/mapswipe/mapswipe-backend/commit/f14903ab1acc9044e19fee7c799eea99d7890d96))
- *(serializer)* Allow plain text in aoi validation - ([a03cd0e](https://github.com/mapswipe/mapswipe-backend/commit/a03cd0e914a15e0f9e3ed84c1d0277d69e52cc71))

#### 🐛 Bug Fixes

- *(project)* Fix organization archive validation - ([3eb742b](https://github.com/mapswipe/mapswipe-backend/commit/3eb742b53b012035e00ed948e57fdb6438019c1d))
- *(project)* Use project and tutorial type on update status response - ([a87b752](https://github.com/mapswipe/mapswipe-backend/commit/a87b752f5b666545bc8c59057a13ff3c6d5f786d))
- *(serializer)* Fix serialization of object_errors - ([6b68d9c](https://github.com/mapswipe/mapswipe-backend/commit/6b68d9c7d48b47e046d682db869ab773d4a0aff2))
- *(typing)* Fix typing issues with assertions and null checks - ([5de963b](https://github.com/mapswipe/mapswipe-backend/commit/5de963bb14b8f06d754cf0fd0ddd99c56c78525b))

#### 🚜 Refactor

- *(typing)* Add type hints on added fields - ([603d9a6](https://github.com/mapswipe/mapswipe-backend/commit/603d9a6349cba01b90f5536dbb8805f3008e9b10))
- *(typing)* Add typing in django fields - ([cb40cf9](https://github.com/mapswipe/mapswipe-backend/commit/cb40cf93653dfee89a30e7506c06fc8c740cbdb9))
- *(validate)* Use custom_fields instead of manually defining types - ([de99350](https://github.com/mapswipe/mapswipe-backend/commit/de99350e6d3e8a64c5746d0e3c72428ea9623f23))

#### 🧪 Testing

- *(tutorial)* Add test for publishing a tutorial - ([e7596e8](https://github.com/mapswipe/mapswipe-backend/commit/e7596e8569794f71b7040a46f19008f82df46370))

#### ⚙️ Miscellaneous Tasks

- *(base)* Separate max time spend percentile - ([677291c](https://github.com/mapswipe/mapswipe-backend/commit/677291ce179d1166975df803f112d60e76218c50))
- *(firebase)* Set target=emulator for firebase - ([0dd5fa3](https://github.com/mapswipe/mapswipe-backend/commit/0dd5fa389b9e74339d739f0029ce63326911717b))
- *(migration)* Create merge migration - ([5186787](https://github.com/mapswipe/mapswipe-backend/commit/51867874dec9db7af42ead609fec9eced67edde4))
- *(mutation)* Add mutation for updating project status - ([e643904](https://github.com/mapswipe/mapswipe-backend/commit/e643904da8255bd52e0beca64a71ee584d1db83a))
- *(mutation)* Add mutation for updating project status - ([4a071e7](https://github.com/mapswipe/mapswipe-backend/commit/4a071e7e67b8a14052211038eadfc4a56e8b631d))
- *(precommit)* Add pyupgrade, merge conflict, test naming - ([5419474](https://github.com/mapswipe/mapswipe-backend/commit/541947440ae017920e27616cc8bb0720b9cd0839))
- *(testcase)* Add test case for firebase push. - ([479b34d](https://github.com/mapswipe/mapswipe-backend/commit/479b34d0dd57cee0abc191323cba5bafd5423b4b))
- *(tutorial)* Add api to update tutorial status - ([cf99553](https://github.com/mapswipe/mapswipe-backend/commit/cf995537f6c3e52aa64ceb93c456a9d56311c156))
- *(typing)* Enable monkeypatching for django stubs ext - ([f53b8b6](https://github.com/mapswipe/mapswipe-backend/commit/f53b8b69f53801a80154b102451294e3fb2574ce))

### 🍻 Pull Requests (9)
- (#115) [Breaking: Mutation for project and tutorial state change](https://github.com/mapswipe/mapswipe-backend/pull/115)
- (#124) [FirebaseTestcase: add test case for firebase push.](https://github.com/mapswipe/mapswipe-backend/pull/124)
- (#125) [Feature/Project instruction](https://github.com/mapswipe/mapswipe-backend/pull/125)
- (#126) [Separate max time spend percentile](https://github.com/mapswipe/mapswipe-backend/pull/126)
- (#127) [Feat(asset): Add mapswipe-assets as submodule](https://github.com/mapswipe/mapswipe-backend/pull/127)
- (#128) [Allow plain text in aoi validation](https://github.com/mapswipe/mapswipe-backend/pull/128)
- (#129) [Feat(results): process partial data](https://github.com/mapswipe/mapswipe-backend/pull/129)
- (#130) [Feat(cron): setup a cron job to fetch users from firebase](https://github.com/mapswipe/mapswipe-backend/pull/130)
- (#131) [Feat(firebase): disable firebase functions on test](https://github.com/mapswipe/mapswipe-backend/pull/131)


## [0.2.0-dev2](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.0-dev1..v0.2.0-dev2) - 2025-08-25
### Changes:

#### 🚀  Features

- *(asset)* Remove mimetype from asset mutation - ([8f65f3c](https://github.com/mapswipe/mapswipe-backend/commit/8f65f3ca29a0323632b1f8d6507ecf3ca410ed98))
- *(asset)* [**breaking**] Add external_url and input_type on project assets - ([536960c](https://github.com/mapswipe/mapswipe-backend/commit/536960c03056c2206aa174aed404bcd3cf227638))
- *(data-migration)* Fetch manager's email from firebase - ([e027ca3](https://github.com/mapswipe/mapswipe-backend/commit/e027ca37b93c9de25e564a0d48d830dbe4462b42))
- *(exports)* Add export logic from existing system - ([f2d57e5](https://github.com/mapswipe/mapswipe-backend/commit/f2d57e54f98b0a0ec91c94b7b0befc35b30dc0ac))
- *(firebase)* Pull contributor user from firebase - ([81c1543](https://github.com/mapswipe/mapswipe-backend/commit/81c1543f918fe0f95dddf71fecfee397af1bc042))
- *(firebase)* Use absolute uri while using asset in firebase - ([ace7a21](https://github.com/mapswipe/mapswipe-backend/commit/ace7a21e161fe0fb805908dbc614a9129c1738c6))
- *(mapping)* Pull mapping from firebase - ([44e4282](https://github.com/mapswipe/mapswipe-backend/commit/44e4282542ea02b6e64fc1e133dfd51b6f04fc96))
- *(project-test)* Use real image in test - ([bf3a7d0](https://github.com/mapswipe/mapswipe-backend/commit/bf3a7d0f41e072f37b627fdaad6867e11d6ab9f5))
- *(serializer)* Change the mimetype check from mimetypes to python-magic. - ([571e8c1](https://github.com/mapswipe/mapswipe-backend/commit/571e8c1d1d5242a455be358cc803757257883363))
- *(validate-image)* [**breaking**] Handle generation of tutorial data on firebase - ([2d8e260](https://github.com/mapswipe/mapswipe-backend/commit/2d8e260a4723879958c9984a5deb769b98402d92))
- *(validate-image)* Increase max image asset count for object image - ([2c58b78](https://github.com/mapswipe/mapswipe-backend/commit/2c58b789c9b66c06d4878a2cf368a9d33da9aece))
- *(validate-image)* Add specifics for tutorial - ([35c4224](https://github.com/mapswipe/mapswipe-backend/commit/35c42244db72c723c143cf236c6e82ddf4366183))
- *(validate-image)* Implement processing of validate image - ([8152d2c](https://github.com/mapswipe/mapswipe-backend/commit/8152d2cb1828f9101188d22e8ab75723c58d4c1f))
- *(validate-image)* Update project specifics - ([be63a7c](https://github.com/mapswipe/mapswipe-backend/commit/be63a7c2b0e6f80c898ee9411abc1f7031ecd3f9))
- [**breaking**] Add MANAGER_DASHBOARD_DOMAIN, COMMUNITY_DASHBOARD_DOMAIN config - ([b95c1cf](https://github.com/mapswipe/mapswipe-backend/commit/b95c1cf3b80244270c663a2aedfe629c6ad124f5))

#### 🐛 Bug Fixes

- *(asset)* [**breaking**] Rename objectImage to object_image - ([51faa81](https://github.com/mapswipe/mapswipe-backend/commit/51faa81a7f576a15be80366866ece209849e5200))
- *(asset)* [**breaking**] Clear older DEBUG related project assets - ([a6519c4](https://github.com/mapswipe/mapswipe-backend/commit/a6519c4cf2d6324809562ea48510f244e72909af))
- *(asset)* Disable geojson validation on asset upload - ([d8a061e](https://github.com/mapswipe/mapswipe-backend/commit/d8a061e63fe22dde005081df8983e84486c38aab))
- *(export)* Add typings - ([3a0df80](https://github.com/mapswipe/mapswipe-backend/commit/3a0df80413779c0fa853fcd081329ec5ce4b832b))
- *(file)* Add is_file_empty to check for file with empty content - ([aa0a3c5](https://github.com/mapswipe/mapswipe-backend/commit/aa0a3c5cd097e8af6d34dd0b10110fccd3dec757))
- *(filter)* [**breaking**] Fix typo on usergroup filter - ([61a3907](https://github.com/mapswipe/mapswipe-backend/commit/61a3907ac24d71e794313d8cdba31f5e324ffb51))
- *(firebase)* Use feature id instead of index for validate task - ([816239f](https://github.com/mapswipe/mapswipe-backend/commit/816239f2154c89f2a68c070aa5fe6420770eca57))
- *(firebase)* Use correct key for synchronizing organisations - ([74c149c](https://github.com/mapswipe/mapswipe-backend/commit/74c149c0e64c65e8fd2def11751fc50ef44c053b))
- *(firebase)* Change sync to firebase to synchronous - ([4132917](https://github.com/mapswipe/mapswipe-backend/commit/4132917974a952c3dee3852513f229b92613352d))
- *(firebase-auth)* Add firebase-auth url to allowed cors urls - ([467a2ca](https://github.com/mapswipe/mapswipe-backend/commit/467a2cacacf4cffac350323e06bf34c8d93f5b06))
- *(pydantic)* Use model_validate instead of spreading dict - ([37f7070](https://github.com/mapswipe/mapswipe-backend/commit/37f7070452cb0efbfae602707b41fb52c82b5cb3))
- *(settings)* Handle None values on urlparse - ([8c3787a](https://github.com/mapswipe/mapswipe-backend/commit/8c3787ae256d76a2538f8e82e9a13f7a3934b553))
- *(tileserver)* Rename quadkey to quad_key - ([d2cac0d](https://github.com/mapswipe/mapswipe-backend/commit/d2cac0d3293c6f3ef54db34e162583b4a6159fe6))
- *(validate-image)* Convert ids from coco to numeric string - ([f637528](https://github.com/mapswipe/mapswipe-backend/commit/f63752855ea5a8ba90ccd91e019e1203149e5895))

#### 🚜 Refactor

- *(filter)* Replace unaccented_filter decorator with simple func - ([7a3148f](https://github.com/mapswipe/mapswipe-backend/commit/7a3148f1d7182ca1e430a3a57b7e05fb7de8a650))
- *(firebase)* Use bulk_create to create/update users - ([bdd644a](https://github.com/mapswipe/mapswipe-backend/commit/bdd644a49586c5306e696775858c75e112fb59ec))
- *(project)* Rename Project Asset: Stats -> Exports - ([57d9379](https://github.com/mapswipe/mapswipe-backend/commit/57d9379547ec9ea5a41485c237ba170a501e4075))
- *(raster-tile)* Add min and max zoom - ([d20cb9e](https://github.com/mapswipe/mapswipe-backend/commit/d20cb9e3b4050ad84106ad82377f5a407ece779c))
- *(user)* Change fb_uid to contributor user - ([40b4f58](https://github.com/mapswipe/mapswipe-backend/commit/40b4f588a2fe809388a49ec9c80c16d16c38958a))
- *(validate)* Move feature grouping logic to utils - ([3cd99cf](https://github.com/mapswipe/mapswipe-backend/commit/3cd99cf8a0d88418eaa81b087d1d89b923c677fa))

#### ⚙️ Miscellaneous Tasks

- *(admin)* Add DELETE, UPDATE and ADD permission to false in admin. - ([d72bf2e](https://github.com/mapswipe/mapswipe-backend/commit/d72bf2e6383f3a2d16e6a94fb96601af3438830c))
- *(admin)* Make admin fields readonly - ([949f532](https://github.com/mapswipe/mapswipe-backend/commit/949f53250a18f7cc534efe407ebe4a55495373ec))
- *(filter)* Add decorator for unaccented string filter - ([59e9d25](https://github.com/mapswipe/mapswipe-backend/commit/59e9d25e653aef5e3cabe5c39ae0358a3aeb3dd1))
- *(filter)* Add unaccented string filter for char fields. - ([0a3fe5c](https://github.com/mapswipe/mapswipe-backend/commit/0a3fe5ca9169f91c5351f2b168fede1ab1bf047b))
- *(firebase)* Set firebase push status to PENDING before triggering - ([8128f79](https://github.com/mapswipe/mapswipe-backend/commit/8128f799dff7ab234d8aa1bb4a629ea97bb6f411))
- *(firebase)* Use firebase functions with pnpm - ([43e0ca3](https://github.com/mapswipe/mapswipe-backend/commit/43e0ca3ac8465badb54f137cd7c228ba421ddd43))

### 🍻 Pull Requests (12)
- (#96) [Fix/data migration](https://github.com/mapswipe/mapswipe-backend/pull/96)
- (#104) [Feat/image mimetype check](https://github.com/mapswipe/mapswipe-backend/pull/104)
- (#105) [Fix(tileserver): rename quadkey to quad_key](https://github.com/mapswipe/mapswipe-backend/pull/105)
- (#108) [Feature/asset types](https://github.com/mapswipe/mapswipe-backend/pull/108)
- (#110) [Firebase: change sync to firebase task to synchronous](https://github.com/mapswipe/mapswipe-backend/pull/110)
- (#111) [Filter: Unaccented string filter for char fields.](https://github.com/mapswipe/mapswipe-backend/pull/111)
- (#112) [Admin: make admin fields readonly](https://github.com/mapswipe/mapswipe-backend/pull/112)
- (#113) [Feat(firebase): pull contributor user from firebase](https://github.com/mapswipe/mapswipe-backend/pull/113)
- (#116) [Fix(firebase-auth): add firebase-auth url to allowed cors urls](https://github.com/mapswipe/mapswipe-backend/pull/116)
- (#117) [Firebase: set firebase push status to PENDING before triggering](https://github.com/mapswipe/mapswipe-backend/pull/117)
- (#120) [Feat: Results pull and Export](https://github.com/mapswipe/mapswipe-backend/pull/120)
- (#121) [Feat!: add MANAGER_DASHBOARD_DOMAIN, COMMUNITY_DASHBOARD_DOMAIN config](https://github.com/mapswipe/mapswipe-backend/pull/121)


## [0.2.0-dev1](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.0-dev0..v0.2.0-dev1) - 2025-08-06
### Changes:

#### 🚀  Features

- *(admin)* Remove inline contributor user create on team - ([a38f69b](https://github.com/mapswipe/mapswipe-backend/commit/a38f69b74965d5a13ed1d2b10547f6bb607195a6))
- *(asset)* Add validation checks for geojson data - ([deec09b](https://github.com/mapswipe/mapswipe-backend/commit/deec09b9d5a2343a3c54cd7a79be40a4c445e720))
- *(asset)* Remove size type from the MapswipeDjangoFileType - ([90f7bdd](https://github.com/mapswipe/mapswipe-backend/commit/90f7bdde7d868b3cc22c2747afdce19f322f94c2))
- *(asset)* Add common asset mixing for project and tutorial - ([5715995](https://github.com/mapswipe/mapswipe-backend/commit/57159954e4269736b5adc4de3a419c309b14256a))
- *(ci)* Add docker logs in "Start app resources" after failure - ([19abb35](https://github.com/mapswipe/mapswipe-backend/commit/19abb3583f7a6d23c54b2febde343539f6d0d95d))
- *(data-migration)* Add script to load data from existing_database - ([5a130fe](https://github.com/mapswipe/mapswipe-backend/commit/5a130feeab0993d46f4d9999d6a01de1b8f78d48))
- *(data-migration)* Pre management command changes - ([a97734e](https://github.com/mapswipe/mapswipe-backend/commit/a97734ea1efbd5bfab77e84e3e2c234849126237))
- *(data-migration)* Setup app for existing_database - ([445a9ae](https://github.com/mapswipe/mapswipe-backend/commit/445a9ae381db893286e3f61e8bda96774684fb13))
- *(firebase)* Setup Firebase bulk manager for set and update - ([ebcad80](https://github.com/mapswipe/mapswipe-backend/commit/ebcad80abc80c72459eb2ad1759741ba99a4592c))
- *(firebase)* Sync (push) tutorial to firebase - ([b76b606](https://github.com/mapswipe/mapswipe-backend/commit/b76b6061bc60d6f091f1d336673937ba26d68b1e))
- *(firebase)* Support pushing find/compare/completeness tutorial data to firebase - ([5cc5cc7](https://github.com/mapswipe/mapswipe-backend/commit/5cc5cc7fd62c8fbd751870348f221a5c7db1e6a4))
- *(firebase)* Setup base for pushing tutorial data to firebase - ([2300cc0](https://github.com/mapswipe/mapswipe-backend/commit/2300cc0b9bd72fa6e359c039f87d9097294ff96a))
- *(firebase)* Allow extra fields when validating data from firebase - ([16a6016](https://github.com/mapswipe/mapswipe-backend/commit/16a60163b2df5d1855b751d00ae58cd11fe4013b))
- *(firebase)* Validate data before updating the data - ([264b649](https://github.com/mapswipe/mapswipe-backend/commit/264b6498dabee774c06c55915b62f355a2189308))
- *(firebase)* Introduce firebase_id to replace canonical_id - ([2a7b43e](https://github.com/mapswipe/mapswipe-backend/commit/2a7b43e44f50d39cbe2d70fdae6ebb99397afe1d))
- *(project)* Add compression feature for the tasks - ([45361f1](https://github.com/mapswipe/mapswipe-backend/commit/45361f1c584b672338d6ba8e8fbd94908ed06847))
- *(project)* Add export project asset - ([02b01d4](https://github.com/mapswipe/mapswipe-backend/commit/02b01d4192c10c90f6a36766472996314db9f48d))
- *(projectasset)* Add validations checks on project assets - ([a2e9909](https://github.com/mapswipe/mapswipe-backend/commit/a2e9909cdeda0201091c58e520df4fd0a13a9052))
- *(query)* Add custom option for image validate and normal validate - ([b71033e](https://github.com/mapswipe/mapswipe-backend/commit/b71033edf01f172274d16248eaa2b6f7a619f438))
- *(tutorial)* Add project type on tutorial type - ([f01b81d](https://github.com/mapswipe/mapswipe-backend/commit/f01b81d1bf68b13d5a780249a18465e107d2a72e))
- *(tutorial)* Use tutorial asset for block images - ([ed851ac](https://github.com/mapswipe/mapswipe-backend/commit/ed851ac29453e9bbfeb896bada0011a2cd2aced4))
- *(tutorial)* Add validation check for project on tutorial - ([5dd7ba4](https://github.com/mapswipe/mapswipe-backend/commit/5dd7ba4dec4ca92374367a6b27f6a07eb081bc3c))
- *(tutorial)* State transition for tutorial - ([040f3b3](https://github.com/mapswipe/mapswipe-backend/commit/040f3b3c060fb1e673e2f46ea03487d579df7cc8))
- *(tutorial-asset)* Add Tutorial Asset and validation checks - ([7aebd7d](https://github.com/mapswipe/mapswipe-backend/commit/7aebd7d979f62ec15225bea9eb9e043cf19a4ec2))
- *(validate)* Implement remaining object sources - ([a6e6d93](https://github.com/mapswipe/mapswipe-backend/commit/a6e6d9374b0fed7a25c64a00540f572e48c28049))

#### 🐛 Bug Fixes

- *(asset)* [**breaking**] Send image object instead of pk for tutorial asset - ([5e145f6](https://github.com/mapswipe/mapswipe-backend/commit/5e145f63baa5498df679b77a57463b6c6d627bf7))
- *(assets)* Add client_id on project and tutorial assets - ([b8bfb51](https://github.com/mapswipe/mapswipe-backend/commit/b8bfb51afa239f1eb88b32d639726d7310d8d029))
- *(contributorUserGroups)* Add unique_together for user+user_group - ([422f854](https://github.com/mapswipe/mapswipe-backend/commit/422f854ee1777b4d9aea02a530cdfdedcea28003))
- *(firebase)* Update information_pages on tutorial edit - ([3e3c4d5](https://github.com/mapswipe/mapswipe-backend/commit/3e3c4d59fb4eff2b9576b85d8bd9647145f0a4a9))
- *(firebase)* Fix issue with team and status while syncing to firebase - ([79f59ee](https://github.com/mapswipe/mapswipe-backend/commit/79f59ee25e7192cfc606e5ab4362b6f95167480c))
- *(firebase)* Fix group id pushed to firebase - ([c3ee11f](https://github.com/mapswipe/mapswipe-backend/commit/c3ee11f62dba5d6120539256c797a1f4320ffec3))
- *(firebase)* Add tutorial_ prefix on tutorial firebase id - ([58011a8](https://github.com/mapswipe/mapswipe-backend/commit/58011a8d1b0a6f610ea02b366ee17bfa236d0f6e))
- *(firebase)* Update key used for group and task references - ([6bba0d3](https://github.com/mapswipe/mapswipe-backend/commit/6bba0d32cba5037dc2d4f8cffeb2e06977f0c0b4))
- *(firebase)* Send null to clear values in firebase - ([2c4dc88](https://github.com/mapswipe/mapswipe-backend/commit/2c4dc88ff2e4be59270a11fd1443fbbeb07edeb5))
- *(firebase)* Update firebase push logic for contributor user - ([7aa7207](https://github.com/mapswipe/mapswipe-backend/commit/7aa7207c65080867436c1b668d910953c857fea3))
- *(migration)* Rebase and merge migrations - ([fff11f5](https://github.com/mapswipe/mapswipe-backend/commit/fff11f5ec403a6c0cac487ff2c09de04067e5dc9))
- *(task)* Geojson load issue on project task geometry - ([1f9ed32](https://github.com/mapswipe/mapswipe-backend/commit/1f9ed325a4e1444d6bd51983c5035b080bfbd5bc))
- *(tutorial)* Remove project from tutorial update serializer - ([cc25d41](https://github.com/mapswipe/mapswipe-backend/commit/cc25d41b03db6dfd5c651c8945b96020ddb979f1))
- *(validate)* Fix issue with task grouping - ([cb7eb0c](https://github.com/mapswipe/mapswipe-backend/commit/cb7eb0c40add9803339219a8ce72fcbbb031517b))
- *(validate-project)* Load geojson for the geometry in validate-project - ([3cd6213](https://github.com/mapswipe/mapswipe-backend/commit/3cd62134e03d42562da6c7ad8968ab0b4b483358))

#### 🚜 Refactor

- *(asset)* Change asset mixin to asset serializer - ([f21bdee](https://github.com/mapswipe/mapswipe-backend/commit/f21bdee0fc2fea327d00895ca8993e472c20587f))
- *(contributor)* Rename user_id to firebase_id for ContributorUser - ([6d99101](https://github.com/mapswipe/mapswipe-backend/commit/6d99101bfa608242bf485d414c45e0e0acc5d346))
- *(firebase)* Remove unused function push_django_to_firebase - ([135ac25](https://github.com/mapswipe/mapswipe-backend/commit/135ac2581dec18be55478c686037d2615771c2c8))
- *(firebase)* Rename method names for project and tutorial sync - ([89d6a5d](https://github.com/mapswipe/mapswipe-backend/commit/89d6a5da5657896453a861ea835fbb251fb68b13))
- *(firebase)* Add to_firebase method on enum for transformation - ([16d9ade](https://github.com/mapswipe/mapswipe-backend/commit/16d9ade4a5cac50dab956293a636e2ab36a9aa4f))
- *(validate)* Cleanup hot_tm_url generation - ([11ca640](https://github.com/mapswipe/mapswipe-backend/commit/11ca640064ee2bad6f9dbca5e319e5a83c62813f))

#### 🧪 Testing

- *(tutorial)* Add validation of CUD inputs with empty list input - ([b521d82](https://github.com/mapswipe/mapswipe-backend/commit/b521d82ce7c2c63c08b87a57dec9a8c4e99350ea))

#### ⚙️ Miscellaneous Tasks

- *(admin)* Restrict user to add membership in archived team. - ([cbb3cb3](https://github.com/mapswipe/mapswipe-backend/commit/cbb3cb35a9883b8a4b7cbdd6dc0f418284e83eb7))
- *(admin)* Add a common firebase resource admin. - ([81d4d04](https://github.com/mapswipe/mapswipe-backend/commit/81d4d048ff9fe5cc309da539d22abd2c23536fcd))
- *(admin)* Add management command to create dummy contributor user - ([1e1e33e](https://github.com/mapswipe/mapswipe-backend/commit/1e1e33e3c34b5b0c84fc3cd77c885333949681c2))
- *(ci)* Move firebase-test before docker build - ([3209921](https://github.com/mapswipe/mapswipe-backend/commit/32099216c60c5ac6fdd0e42063c3ca27511b0b15))
- *(contributor)* Remove obsolete user_id filter - ([09dfc92](https://github.com/mapswipe/mapswipe-backend/commit/09dfc9245556ce91fe17f131966e1115a9b03dfe))
- *(contributor-team)* Sync team member to firebase when team update or create - ([6428b85](https://github.com/mapswipe/mapswipe-backend/commit/6428b85d315bb862938eb063960a29cb2262ce33))
- *(firebase)* Use schema with optional lists and mappings in firebase - ([0050efa](https://github.com/mapswipe/mapswipe-backend/commit/0050efa9ba987fdf311afd4eedf335178f699014))
- *(firebase)* Sync user group to firebase. - ([1ab8614](https://github.com/mapswipe/mapswipe-backend/commit/1ab86146b2482e97bf5eb62e2083e435a980c02d))
- *(firebase)* Update sub-module with yarn+git install fix - ([67871be](https://github.com/mapswipe/mapswipe-backend/commit/67871bef0372ebfcdf585a3987bb7220aa5f7d2d))
- *(firebase)* Sync team members to firebase while removing team member - ([098e266](https://github.com/mapswipe/mapswipe-backend/commit/098e266419137ff4041c79221b5dc3435a002d88))
- *(firebase)* Add common func for push_to_firebase - ([b1375f5](https://github.com/mapswipe/mapswipe-backend/commit/b1375f59380938312e508625188dd703e5089882))
- *(migration)* Generate migration for tutorialasset - ([2ef2ecc](https://github.com/mapswipe/mapswipe-backend/commit/2ef2ecc83024d7a079ad7047f35a8ef23c1e85d1))
- *(migrations)* Add a merge migration - ([c24bd9d](https://github.com/mapswipe/mapswipe-backend/commit/c24bd9d3cb338f59d629c0f1c2324eab2b7463da))
- *(migrations)* Add a merge migration - ([78c9a56](https://github.com/mapswipe/mapswipe-backend/commit/78c9a56e0d7e7d159f4754dfb3cbd345c5be23d0))
- *(migrations)* Rebase and merge the migrations - ([9e4fe65](https://github.com/mapswipe/mapswipe-backend/commit/9e4fe657b63b9010bc8db927aeb64d3695b77769))
- *(test)* Add unit test. - ([89e3ab0](https://github.com/mapswipe/mapswipe-backend/commit/89e3ab05c88d5ab1691e9f85deafceb249fab4a1))

### 🍻 Pull Requests (18)
- (#68) [Breaking! Tutorial state transition and asset ](https://github.com/mapswipe/mapswipe-backend/pull/68)
- (#83) [Feature/sync team member to firebase](https://github.com/mapswipe/mapswipe-backend/pull/83)
- (#84) [Add validation checks for geojson asset](https://github.com/mapswipe/mapswipe-backend/pull/84)
- (#85) [Remove size field from the MapswipeDjangoFileType](https://github.com/mapswipe/mapswipe-backend/pull/85)
- (#86) [Feat/data migration](https://github.com/mapswipe/mapswipe-backend/pull/86)
- (#87) [Feat(tutorial): use tutorial asset for block images](https://github.com/mapswipe/mapswipe-backend/pull/87)
- (#88) [Send NULL to firebase to enable clearing data](https://github.com/mapswipe/mapswipe-backend/pull/88)
- (#89) [Firebase: Sync user group](https://github.com/mapswipe/mapswipe-backend/pull/89)
- (#90) [ContributorUser: Cannot add member to archived team.](https://github.com/mapswipe/mapswipe-backend/pull/90)
- (#91) [Feat: push firebase data for find, compare, completensss and validate tutorial](https://github.com/mapswipe/mapswipe-backend/pull/91)
- (#93) [Feat: Task compression on validate project](https://github.com/mapswipe/mapswipe-backend/pull/93)
- (#94) [Feat/custom option](https://github.com/mapswipe/mapswipe-backend/pull/94)
- (#98) [Add project type on tutorial type](https://github.com/mapswipe/mapswipe-backend/pull/98)
- (#99) [Implement remaining object sources for validate project](https://github.com/mapswipe/mapswipe-backend/pull/99)
- (#100) [Fix issue on task geometry json load](https://github.com/mapswipe/mapswipe-backend/pull/100)
- (#101) [Feat/tutorial firebase push](https://github.com/mapswipe/mapswipe-backend/pull/101)
- (#102) [Add Unit Test](https://github.com/mapswipe/mapswipe-backend/pull/102)
- (#103) [Feature: Firebase Bulk upload](https://github.com/mapswipe/mapswipe-backend/pull/103)

### :tada: New Contributors (1)

- [@AdityaKhatri](https://github.com/AdityaKhatri) made their first contribution in [#87](https://github.com/mapswipe/mapswipe-backend/pull/87)

## [0.2.0-dev0](https://github.com/mapswipe/mapswipe-backend/compare/v0.1.0..v0.2.0-dev0) - 2025-07-30
### Changes:

#### 🚀  Features

- *(admin-panel)* Enhance admin panel for project and tutorial apps - ([1ab0c16](https://github.com/mapswipe/mapswipe-backend/commit/1ab0c16b51c0b736dd7c259323d93e51bf333574))
- *(api)* Update min_zoom, max_zoom, source_name and credits for vector tile - ([5c30181](https://github.com/mapswipe/mapswipe-backend/commit/5c301815e1fd228b55d619c33792f0418e2ac236))
- *(api)* Add pre-defined layers for vector tiles - ([cfaa7f6](https://github.com/mapswipe/mapswipe-backend/commit/cfaa7f6393780379eb0b5e63df5f681a4e9502f5))
- *(api)* Add contributor user group create/update mutation - ([8943c5e](https://github.com/mapswipe/mapswipe-backend/commit/8943c5ebf28b053807765d539bf47311bb6adc31))
- *(api)* Add organization update mutation - ([c653c34](https://github.com/mapswipe/mapswipe-backend/commit/c653c340089f8cf0859ba6e95520cd1c863c7886))
- *(ci)* Add commit lint - ([b7ae327](https://github.com/mapswipe/mapswipe-backend/commit/b7ae3277470ee81cdb715a39992874e7ac474c5a))
- *(ci)* Delegate builds to bake for better perf - ([88e9de8](https://github.com/mapswipe/mapswipe-backend/commit/88e9de8917e236984820de5cbb3077f01a8be8f1))
- *(common)* Add archivable resources generic serializer - ([8dda6ae](https://github.com/mapswipe/mapswipe-backend/commit/8dda6ae2dadeeecc80a01ea920661746a81530ef))
- *(completeness)* Update project specifics to support vector tiles - ([e5ca920](https://github.com/mapswipe/mapswipe-backend/commit/e5ca9200c0e125aafcb0f4d11c03a96ff36128a3))
- *(custom_options)* Add custom options to validate and validate_image - ([15bef04](https://github.com/mapswipe/mapswipe-backend/commit/15bef04823638774c0b04eef4594b2b462d15d14))
- *(firebase)* Add canonical id for firebase models - ([ebcd630](https://github.com/mapswipe/mapswipe-backend/commit/ebcd630e3fe05b0813c295ff292a5414da5e2e80))
- *(firebase)* Add overlay layer in completeness - ([8b37c47](https://github.com/mapswipe/mapswipe-backend/commit/8b37c47f4ef31d50d353bcb0630231a4271a8732))
- *(firebase)* Use fallback image for completeness - ([f514ac2](https://github.com/mapswipe/mapswipe-backend/commit/f514ac2ac8b63aff98c51ae39fc2d4a9a3f115f8))
- *(firebase)* Set legacy task and group id - ([5cecb4f](https://github.com/mapswipe/mapswipe-backend/commit/5cecb4fcceae0b89b5a688b11620367638b8dfaf))
- *(firebase)* Add legacy id in project tasks and groups - ([3b6b047](https://github.com/mapswipe/mapswipe-backend/commit/3b6b047fe66d6ff0d73922edef1cee1161b796f9))
- *(firebase)* Add test for authentication - ([bd4b97b](https://github.com/mapswipe/mapswipe-backend/commit/bd4b97b63a8dd9e1229cc40e668452bc58f61a58))
- *(firebase)* Add authentication with firebase - ([d48936c](https://github.com/mapswipe/mapswipe-backend/commit/d48936cdb8e44ed6f963e0dcb3e4a5745a705cb7))
- *(firebase)* Implement project specifics for project, task and group - ([7651488](https://github.com/mapswipe/mapswipe-backend/commit/7651488bb0804703fce556cf12932782ec091d5e))
- *(firebase)* Sync tasks and groups on firebase - ([df00a4c](https://github.com/mapswipe/mapswipe-backend/commit/df00a4c0170f9276aad51a4ab21817c557ed313f))
- *(firebase)* Setup test environment for firebase - ([66a2747](https://github.com/mapswipe/mapswipe-backend/commit/66a274767da9f808a1e95a99c6658c56d889f2b1))
- *(firebase)* Add project specific handlers for compare and completeness - ([8ba8d29](https://github.com/mapswipe/mapswipe-backend/commit/8ba8d2948fdb56622abeb8bd725ed13617da92e8))
- *(firebase)* Add handlers for creating and updating a project in firebase - ([5308ed3](https://github.com/mapswipe/mapswipe-backend/commit/5308ed32dd0abda93c44ccf84fbd61ce3727369b))
- *(firebase)* Integrate firebase emulator - ([79ac332](https://github.com/mapswipe/mapswipe-backend/commit/79ac3329b2ea29cb59f6e871740313bd6b0736b8))
- *(name)* Update project name format - ([1d13db9](https://github.com/mapswipe/mapswipe-backend/commit/1d13db984e741d1861098373e33eef4885432eef))
- *(ordering)* Add ordering for project name - ([81ea6f6](https://github.com/mapswipe/mapswipe-backend/commit/81ea6f6b2b662e745ad09e887d0eb857a319fb56))
- *(organization)* Set default filtering on organization query - ([26d511a](https://github.com/mapswipe/mapswipe-backend/commit/26d511a82200892630212e3bf9ce672bcabd0674))
- *(organization)* Archive and unarcive organization. - ([a662628](https://github.com/mapswipe/mapswipe-backend/commit/a6626285087da6bd670fd7221ccbd75a4531aa2d))
- *(project)* Set default filtering on project and tutorial - ([052c054](https://github.com/mapswipe/mapswipe-backend/commit/052c054746dc9ac4f712082be1ccfed6d7343e56))
- *(project)* Add validation check for team on project - ([d624848](https://github.com/mapswipe/mapswipe-backend/commit/d624848ad5426793e6857c24ea403fdcf912eec2))
- *(project)* Add new generated name for the project - ([8537bdc](https://github.com/mapswipe/mapswipe-backend/commit/8537bdcfbd7b873346b688506852c548c0d22a41))
- *(project)* Add validation checks for the organization on project - ([277d429](https://github.com/mapswipe/mapswipe-backend/commit/277d429099de8bb53e846195d6cb614168feb0b0))
- *(project)* Archive project - ([ace7ee7](https://github.com/mapswipe/mapswipe-backend/commit/ace7ee74b69ee46392123a7ac24f55f62dfef3f5))
- *(project)* Add test cases for the filtering on projects - ([a85993c](https://github.com/mapswipe/mapswipe-backend/commit/a85993c7bfa46f695ad0f460c34498ce4fc3cd8b))
- *(project-name)* Replace name on filters and order - ([528e585](https://github.com/mapswipe/mapswipe-backend/commit/528e585a5f8d64ac24a12b15340d8d7dc4ccf668))
- *(query)* Add default filters on query - ([2a88cd7](https://github.com/mapswipe/mapswipe-backend/commit/2a88cd76ed6af4dbf2c00361c389c41d7ff31035))
- *(release)* Improve ux on release script - ([87a54ad](https://github.com/mapswipe/mapswipe-backend/commit/87a54ad84041c36ba9032d73d5fe8f2d6d68b1c7))
- *(team)* Add member list to team query - ([dfe7b9c](https://github.com/mapswipe/mapswipe-backend/commit/dfe7b9cd7d6def79deab1c0d9d95a8d16b8cc2a4))
- *(team)* Add query for team - ([6374ba6](https://github.com/mapswipe/mapswipe-backend/commit/6374ba6a1b8518539dba5438656f13823ce76a65))
- *(team)* Add new team feature to a project - ([36dcd75](https://github.com/mapswipe/mapswipe-backend/commit/36dcd75e94c567a88e19adff18df8ece5850b678))
- *(test)* Update test cases for the default queries - ([1081c54](https://github.com/mapswipe/mapswipe-backend/commit/1081c547318cb8fcb1885b0ced62ef566cc0ec5f))
- *(tiles)* Update vector tile urls - ([50fa1b7](https://github.com/mapswipe/mapswipe-backend/commit/50fa1b7512901db11031e59c0519be5749725964))
- *(tiles)* Add static endpoint for tile configuration - ([0957406](https://github.com/mapswipe/mapswipe-backend/commit/09574069b0bfd748df2b2ece0fd7503eb389f771))
- *(tileserver)* Remove tileserver urls from tasks table - ([73759c5](https://github.com/mapswipe/mapswipe-backend/commit/73759c5248fd28b7688c7eb04101e282e0206572))
- *(tileserver)* Remove apiKey substitution on urls in firebase projects - ([104c218](https://github.com/mapswipe/mapswipe-backend/commit/104c218335c6dde22025f5c4ba01777d304a9228))
- *(tutorial)* Add validation checks for status transitions - ([40d4a06](https://github.com/mapswipe/mapswipe-backend/commit/40d4a068f1dc947ef1050b369f151bc713e6763f))
- *(tutorial)* Add test cases for tutorial query and filters - ([e2cb70c](https://github.com/mapswipe/mapswipe-backend/commit/e2cb70c94682aea4f7f54da95f776aaae3e4192b))
- *(user)* Add anonymizeEmail field - ([0d6a1dd](https://github.com/mapswipe/mapswipe-backend/commit/0d6a1dd35580b4d76de69422e70e57639ea50c6b))
- *(validate-image)* Add base inputs, types and pydantic models - ([ddf0a5d](https://github.com/mapswipe/mapswipe-backend/commit/ddf0a5db0a80cd6584e43b515c6b80cf2b5bd5b2))
- *(validation)* Add pydantic validation on nested json fields - ([c645e35](https://github.com/mapswipe/mapswipe-backend/commit/c645e350b063eacb7beb303da67208698dc9f346))
- Add config to enable/disable graphiql - ([eb47ded](https://github.com/mapswipe/mapswipe-backend/commit/eb47ded722b180ebf0f4bfa4bf1896d013f4bc96))

#### 🐛 Bug Fixes

- *(completeness)* [**breaking**] Sync source_layer to firebase for completeness project - ([3c2e74e](https://github.com/mapswipe/mapswipe-backend/commit/3c2e74eec5f969cd17da47d753ac4756db326b11))
- *(dependencies)* Update version for django-debug-toolbar - ([6cf7cdc](https://github.com/mapswipe/mapswipe-backend/commit/6cf7cdc00eb086a675efebccef913a02f6c3046b))
- *(django-debug-tool)* Fix django-tool-bar issue - ([1c08c9d](https://github.com/mapswipe/mapswipe-backend/commit/1c08c9dac99e27c4bfe50c865cefcf824d8499f4))
- *(firebase)* Fix common func for sync to firebase - ([c2c283c](https://github.com/mapswipe/mapswipe-backend/commit/c2c283cfe84b57dd45965d77e673bf84dfeb489a))
- *(firebase)* Use legacy ids for 'validate image' task and group - ([274af0f](https://github.com/mapswipe/mapswipe-backend/commit/274af0f7c04dd058cc16632ea5973b7f555f433e))
- *(firebase)* Fix typo on tmid key while syncing to firebase - ([2723144](https://github.com/mapswipe/mapswipe-backend/commit/2723144b46fe419dbc76407374e3c8e4e0fc42af))
- *(graphql)* Fix interface used error - ([1506b94](https://github.com/mapswipe/mapswipe-backend/commit/1506b9472fb8d259f177486fb99e4bc25b50ed25))
- *(migration)* Rebase and merge migrations for project name - ([5126e11](https://github.com/mapswipe/mapswipe-backend/commit/5126e11d90a6cac1e60b4fe9f8cdb0b2509a8bad))
- *(migration)* Add merge migration - ([8684a00](https://github.com/mapswipe/mapswipe-backend/commit/8684a004f05dd4b1d1750c4627923cd53712b662))
- *(models)* Add old_id on tutorial and user model - ([ddd11f1](https://github.com/mapswipe/mapswipe-backend/commit/ddd11f1cd00159cad07653c83d86e7496ec559b2))
- *(raster-url)* Remove typo - ([9a0a1cb](https://github.com/mapswipe/mapswipe-backend/commit/9a0a1cb441656a76ad2dfcf79421cf91bfc9fc15))
- *(serializer)* Fix typing issues for project and tutorial status - ([4953619](https://github.com/mapswipe/mapswipe-backend/commit/4953619ff5d28d5053c47f5612c452f3ea855d35))
- Fix usages of _StrOrPromise with str() - ([fc99302](https://github.com/mapswipe/mapswipe-backend/commit/fc99302ec5a49ef4c296dce21fb12d2924398a40))
- Update workflow to use new test container - ([c2fe363](https://github.com/mapswipe/mapswipe-backend/commit/c2fe36353a11e5e199f2fcf786ce31dc89a7048c))
- Fixup! refactor(serializer): Inject client_id field automatically in UserResource - ([20e47a8](https://github.com/mapswipe/mapswipe-backend/commit/20e47a887d0398c56a8379f79a326e27fc40b313))

#### 🚜 Refactor

- *(comments)* Add notes on quadkey and open_free_map usage - ([600391d](https://github.com/mapswipe/mapswipe-backend/commit/600391df8f5622965ca1343140a7c9efe6735979))
- *(comments)* Update FIXME and TODO comments - ([4dab061](https://github.com/mapswipe/mapswipe-backend/commit/4dab06190ed524503650777f515798c5884806c3))
- *(core)* Make BaseProject generic for tasks - ([fe294b9](https://github.com/mapswipe/mapswipe-backend/commit/fe294b9bb06c5c63ab4ff0379dc2ab6e5d6e8713))
- *(file-structure)* Move base import - ([6921265](https://github.com/mapswipe/mapswipe-backend/commit/692126522ade3b7fb28482189b774b18165e6b93))
- *(file-structure)* Split tutorial graphql inputs and types - ([0fbdb9d](https://github.com/mapswipe/mapswipe-backend/commit/0fbdb9d98665b48d623bff1e1fe7ce04ac86fa79))
- *(file-structure)* Split project graphql inputs - ([3ad8c1d](https://github.com/mapswipe/mapswipe-backend/commit/3ad8c1de9d65df899f12441a931de207900c187a))
- *(file-structure)* Move project_types to root dir - ([6d2845b](https://github.com/mapswipe/mapswipe-backend/commit/6d2845ba305f16dadb0ec1a298145edc7695d96c))
- *(file-structure)* Separate out utils for raster and vector tiles - ([26a668d](https://github.com/mapswipe/mapswipe-backend/commit/26a668d10c6f29c9e38d3a31c67b362af95603b7))
- *(firebase)* Move core functionality to base project - ([3e8c6c6](https://github.com/mapswipe/mapswipe-backend/commit/3e8c6c6f73002ea8a50fb504874135a2d148caef))
- *(firebase)* Add FIREBASE_HELPER to Config - ([036d3dc](https://github.com/mapswipe/mapswipe-backend/commit/036d3dc042d443771e7cecd9a317274234a8ab12))
- *(general)* Add _ prefix for private class and functions - ([969a289](https://github.com/mapswipe/mapswipe-backend/commit/969a289191a74bbe1fdc57a0352798245b2802a1))
- *(lint)* Update ruff rules and fix/ignore issues - ([34b8ac6](https://github.com/mapswipe/mapswipe-backend/commit/34b8ac694903ebe0047654e71503fdbb7109de12))
- *(models)* Unify enum for icon field - ([d63220c](https://github.com/mapswipe/mapswipe-backend/commit/d63220c75a27858336491b238b4f373589349fe2))
- *(serializer)* Inject client_id field automatically in UserResource - ([f3141da](https://github.com/mapswipe/mapswipe-backend/commit/f3141da8b49b18f5de5ad19f68bf497845f18a5d))
- *(tile-server)* Add raster prefix on raster tile_server - ([abacf14](https://github.com/mapswipe/mapswipe-backend/commit/abacf145c0eb056b912dbebc74a084208d79d7a4))
- *(tile_server)* Rename quad_key to quadkey - ([089567b](https://github.com/mapswipe/mapswipe-backend/commit/089567b469fa9cc61c2fd2e1e51411af47b8aeac))
- *(utils)* Move common functions to utils/store - ([f4f3ec8](https://github.com/mapswipe/mapswipe-backend/commit/f4f3ec8067324572e483be76263e343697692a36))
- *(utils)* Update clean_up_none_keys to support nested arrays - ([722e2ff](https://github.com/mapswipe/mapswipe-backend/commit/722e2ffb9db50b2fd1967153cc7ae248f0fc4434))

#### ⚙️ Miscellaneous Tasks

- *(README)* Update python version in pre-commit-config - ([8c8239b](https://github.com/mapswipe/mapswipe-backend/commit/8c8239b8111bbd2883d3788fa8d2135e921f222e))
- *(firebase)* Add common func for push_to_firebase - ([2d61a1b](https://github.com/mapswipe/mapswipe-backend/commit/2d61a1b2671b9010a6d7ffb939a716bd3c658384))
- *(firebase)* Sync contributor team to firebase - ([67066f0](https://github.com/mapswipe/mapswipe-backend/commit/67066f0ca7d7c7516763fb913c4105153c5a5044))
- *(firebase)* Add base abstract class for firebase resources - ([75a58c0](https://github.com/mapswipe/mapswipe-backend/commit/75a58c041a5edbe8b0c8f07f2cdea6604d3381f0))
- *(migrations)* Merge migrations from develop - ([51bdcab](https://github.com/mapswipe/mapswipe-backend/commit/51bdcab244e89db3b2eaeb5eb39e6bb4f5df1085))
- *(migrations)* Merge migrations from develop - ([e9dba47](https://github.com/mapswipe/mapswipe-backend/commit/e9dba47e558bad8473dd1887005bc5a12bd1e073))
- *(organization)* Sync organization data into firebase. - ([ce454ab](https://github.com/mapswipe/mapswipe-backend/commit/ce454ab52cd71f7935526a990a73ed3a3897fd0d))
- *(project)* Update project name on firebase schema - ([e9a2291](https://github.com/mapswipe/mapswipe-backend/commit/e9a229149fdb96ecde2c1c73b6a3d78331f7ec95))
- *(team)* Add contributor user inline in team page admin panel - ([d34c063](https://github.com/mapswipe/mapswipe-backend/commit/d34c063928fa41bbdfcbb092eeb5b976fcb5b4a6))
- Chore(contributor_team): add validation message when archive non empty
contributor team. - ([bc8ab4a](https://github.com/mapswipe/mapswipe-backend/commit/bc8ab4a7e605a50a15f8f0dd376497a82d45f0eb))
- Move media/static paths to .data - ([588fce4](https://github.com/mapswipe/mapswipe-backend/commit/588fce41ed80e4dff817f88280a29cbc88329a61))
- Generate merge migration and update firebase dependency - ([aba4601](https://github.com/mapswipe/mapswipe-backend/commit/aba4601aa1d944089c0b06e2051e8a81c9a014d9))

### 🍻 Pull Requests (28)
- (#40) [Feature/new completeness](https://github.com/mapswipe/mapswipe-backend/pull/40)
- (#42) [Add mutations for user group and organization](https://github.com/mapswipe/mapswipe-backend/pull/42)
- (#43) [Add pre-defined layers for vector tiles](https://github.com/mapswipe/mapswipe-backend/pull/43)
- (#46) [Refactor file structure for project specifics](https://github.com/mapswipe/mapswipe-backend/pull/46)
- (#47) [Feat(firebase): integrate firebase emulator](https://github.com/mapswipe/mapswipe-backend/pull/47)
- (#50) [Feat: add base inputs, types and pydantic models for validate image project type](https://github.com/mapswipe/mapswipe-backend/pull/50)
- (#51) [Add test cases for project and tutorial](https://github.com/mapswipe/mapswipe-backend/pull/51)
- (#53) [Tutorial state transition validations](https://github.com/mapswipe/mapswipe-backend/pull/53)
- (#54) [Feature/Team](https://github.com/mapswipe/mapswipe-backend/pull/54)
- (#55) [Feat(firebase): add authentication with firebase](https://github.com/mapswipe/mapswipe-backend/pull/55)
- (#56) [Breaking! Split project name](https://github.com/mapswipe/mapswipe-backend/pull/56)
- (#61) [Feat: add config to enable/disable graphiql](https://github.com/mapswipe/mapswipe-backend/pull/61)
- (#62) [Archive: Organization and Project](https://github.com/mapswipe/mapswipe-backend/pull/62)
- (#64) [Add member list on team](https://github.com/mapswipe/mapswipe-backend/pull/64)
- (#65) [Feat/tileserver url gen](https://github.com/mapswipe/mapswipe-backend/pull/65)
- (#66) [Chore/upgrade to django lts](https://github.com/mapswipe/mapswipe-backend/pull/66)
- (#69) [Feature/archive team validation](https://github.com/mapswipe/mapswipe-backend/pull/69)
- (#70) [Chore(organization): sync organization data into firebase.](https://github.com/mapswipe/mapswipe-backend/pull/70)
- (#71) [Add contributor users inline in team page admin panel](https://github.com/mapswipe/mapswipe-backend/pull/71)
- (#72) [Add validation checks for the organization on project](https://github.com/mapswipe/mapswipe-backend/pull/72)
- (#73) [Fix(django-debug-tool): fix django-tool-bar issue](https://github.com/mapswipe/mapswipe-backend/pull/73)
- (#76) [Feature/sync team to firebase](https://github.com/mapswipe/mapswipe-backend/pull/76)
- (#77) [Breaking! unify enum for icon field](https://github.com/mapswipe/mapswipe-backend/pull/77)
- (#78) [Fix django debug toolbar issue](https://github.com/mapswipe/mapswipe-backend/pull/78)
- (#79) [Feature/Set default filtering on queries](https://github.com/mapswipe/mapswipe-backend/pull/79)
- (#80) [Add validation check for team on project](https://github.com/mapswipe/mapswipe-backend/pull/80)
- (#81) [Sync source_layer to firebase for completeness project](https://github.com/mapswipe/mapswipe-backend/pull/81)
- (#82) [Fix(firebase): fix common func for sync to firebase](https://github.com/mapswipe/mapswipe-backend/pull/82)

### :tada: New Contributors (1)

- [@kopitek8](https://github.com/kopitek8) made their first contribution

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

- [@tnagorra](https://github.com/tnagorra) made their first contribution
- [@frozenhelium](https://github.com/frozenhelium) made their first contribution

<!-- generated by git-cliff -->
