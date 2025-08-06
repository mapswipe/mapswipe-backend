# Changelog

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

### :tada: New Contributors (2)

- [@sandeshit](https://github.com/sandeshit) made their first contribution
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
