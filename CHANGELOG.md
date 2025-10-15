# Changelog

## [0.2.4](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.3..v0.2.4) - 2025-10-15
### Changes:

#### 🚀  Features

- *(project)* Update only necessary field to firebase for project stats - ([05b7563](https://github.com/mapswipe/mapswipe-backend/commit/05b756338b4fd08223dfde63944aca1c0809e02d))
- *(public)* Show PAUSED projects in public endpoint - ([c640894](https://github.com/mapswipe/mapswipe-backend/commit/c640894c5b38570521455edfa365752e2a1f2898))
- Feat!(firebase): add FirebaseOrInternalIdInputType

for firebase and internal id support for id for Contributor user and userGroup
BREAKING CHANGE: userId, userGroupId and id for contributor and
community queries are changed - ([f8197b2](https://github.com/mapswipe/mapswipe-backend/commit/f8197b2a0f434d82e9c9a8e27b615c9ccda4e8be))

#### 🐛 Bug Fixes

- *(client-type)* Add missing ios mappings - ([b190c38](https://github.com/mapswipe/mapswipe-backend/commit/b190c3801be1bc6a4810c7295700a3d5d66f8043))
- *(contributor)* Set firebase status initially during sync - ([7321bf3](https://github.com/mapswipe/mapswipe-backend/commit/7321bf3cfc9cfc383e5baa86d4415b53c31bad45))
- *(export)* Use ISO8601 date format for mapping export - ([8ac62f9](https://github.com/mapswipe/mapswipe-backend/commit/8ac62f977e7408789c7072b0d65b643b99091875))
- *(loaddata)* Fix project's status mapping - ([c37f5ac](https://github.com/mapswipe/mapswipe-backend/commit/c37f5ac8513ffe91be2f60ae2af0d64609da0ec7))
- *(loaddata)* Add missing projects's project_type_specifics and description - ([bfcd563](https://github.com/mapswipe/mapswipe-backend/commit/bfcd563307aa81065aee437bb1481cc92a306395))
- *(project)* Handle exceptions from external sources - ([0a6a16a](https://github.com/mapswipe/mapswipe-backend/commit/0a6a16a571582ae6553314199a7b03a5ba8fb270))
- *(project)* Set 0 as default for total_area and number_of_tasks - ([885c55b](https://github.com/mapswipe/mapswipe-backend/commit/885c55bca9827671a5a8f1c1d389a1fca2e14776))
- *(project)* Change default group_size when creating a project - ([e08ff69](https://github.com/mapswipe/mapswipe-backend/commit/e08ff694078e29e06576928264cabd48d0e06ab1))
- *(project)* Fix type for slack_progress_notifications - ([211bd2d](https://github.com/mapswipe/mapswipe-backend/commit/211bd2d925894bca8c9d22b41fd41295197de9d5))
- *(project)* Fix area conversion to km sq - ([cb034ac](https://github.com/mapswipe/mapswipe-backend/commit/cb034ac226e631c743bad908e7830c2399f96f4a))
- *(project)* Update uniqueness constraint on project tasks - ([1b76e14](https://github.com/mapswipe/mapswipe-backend/commit/1b76e14329e4c13c003381d33e65fa4c9c002efe))
- *(release)* Update uv sync command - ([7c57a2d](https://github.com/mapswipe/mapswipe-backend/commit/7c57a2d1682bd000490f662e09005c0e0aef03e1))
- *(slack)* Update project messages - ([01fffc2](https://github.com/mapswipe/mapswipe-backend/commit/01fffc2eba767cba68bb0c6406233caf7c8d0388))
- *(tasks)* Fix use of context manager for redis lock - ([60bf58a](https://github.com/mapswipe/mapswipe-backend/commit/60bf58a7c1bd41d2f6b454ba1914f2f6868513d6))
- *(tileserver)* Remove maxar tile servers from the list - ([2fb8662](https://github.com/mapswipe/mapswipe-backend/commit/2fb86628c6f0d1cc752d99ceb035cae55395de2d))
- *(validate-image)* Use annotation_id instead of image_id when possible - ([8424a73](https://github.com/mapswipe/mapswipe-backend/commit/8424a733a4f164ae8dda751a6ed0117abd69aab3))

#### ⚙️ Miscellaneous Tasks

- *(firebase)* Update submodule for firebase - ([f42c8ce](https://github.com/mapswipe/mapswipe-backend/commit/f42c8ced7a51a29234b166862190cd5aa2f9a6d5))
- *(project)* Add deprecation_reason for project's total_area - ([6836329](https://github.com/mapswipe/mapswipe-backend/commit/683632932c4e7482a2a6b7e789605ad359ce3698))

### 🍻 Pull Requests (1)
- (#200) [Post deployment fixes](https://github.com/mapswipe/mapswipe-backend/pull/200)


## [0.2.3](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.2..v0.2.3) - 2025-10-13
### Changes:

#### 🚀  Features

- *(test)* Add export e2e testing for validate image - ([ce3e43b](https://github.com/mapswipe/mapswipe-backend/commit/ce3e43b7ee2394bd139b00c316c64e43cfd49e18))
- *(user)* Add slack column and filter in admin panel - ([bac54af](https://github.com/mapswipe/mapswipe-backend/commit/bac54af88e16a0a38c15e531290b29f9818d78e7))

#### 🐛 Bug Fixes

- *(export)* Drop duplicate columns on export file - ([3e30aba](https://github.com/mapswipe/mapswipe-backend/commit/3e30abac706ab3cc2757fdf2208e177055429019))
- *(street)* Fix e2e test for street project - ([0876e98](https://github.com/mapswipe/mapswipe-backend/commit/0876e981e4550909e1fdcb9622ef1e377c271778))
- *(test)* Sort task file data with task_id - ([a79131e](https://github.com/mapswipe/mapswipe-backend/commit/a79131e619286b155f7d635b4fa380804280dd00))

#### 🧪 Testing

- *(project)* Remove empty fields from dataset - ([1a9b570](https://github.com/mapswipe/mapswipe-backend/commit/1a9b5703954cdd4ad8510def6300fd8101feb9cd))

#### ⚙️ Miscellaneous Tasks

- *(export)* Skip and track exports for old projects - ([47216da](https://github.com/mapswipe/mapswipe-backend/commit/47216da57d61545aee69ea16fde51122913ec051))
- *(schema)* Generate latest schema.graphql - ([0440b69](https://github.com/mapswipe/mapswipe-backend/commit/0440b69f4eb239910d52ca83b86a888558474dc4))
- *(test)* Update commit HEAD for assets - ([ecbe71b](https://github.com/mapswipe/mapswipe-backend/commit/ecbe71ba59f42a8050676108458b8781fbe0b816))
- *(test)* Update version for shapely and use wkt dump - ([6a06550](https://github.com/mapswipe/mapswipe-backend/commit/6a06550773b295eff9c43d483d5258b942b94e2a))
- *(test)* Update HEAD for the asset file - ([7c3aa8b](https://github.com/mapswipe/mapswipe-backend/commit/7c3aa8b20f205230111c4da182460f3b81728fa2))
- *(test)* Update README file for validate image - ([11032df](https://github.com/mapswipe/mapswipe-backend/commit/11032df5df54cc985f3992f9050bffcc9a178185))
- *(test)* Add export testing for validate project - ([838b174](https://github.com/mapswipe/mapswipe-backend/commit/838b1745b51b548121124de64a4f19cc08e0e6f1))
- *(test)* Add test case for result for street. - ([a1d2a0e](https://github.com/mapswipe/mapswipe-backend/commit/a1d2a0eacea702f567ff32a044d6509496f5b57e))
- *(test)* Add test case for result for validate, validate-image - ([ad18543](https://github.com/mapswipe/mapswipe-backend/commit/ad18543dcb0a912615491687a1bbb7248c9cdcef))

### 🍻 Pull Requests (2)
- (#188) [Result test case for validate, validate-image, street](https://github.com/mapswipe/mapswipe-backend/pull/188)
- (#198) [Fix/export old](https://github.com/mapswipe/mapswipe-backend/pull/198)


## [0.2.2](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.1..v0.2.2) - 2025-10-12
### Changes:

#### 🚀  Features

- *(cron)* Add update_community_dashboard_aggregated_data - ([27bf093](https://github.com/mapswipe/mapswipe-backend/commit/27bf0935e1e025342a98b885d46b505400878e6f))

### 🍻 Pull Requests (1)
- (#196) [Feat(cron): add update_community_dashboard_aggregated_data](https://github.com/mapswipe/mapswipe-backend/pull/196)


## [0.2.1](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.1-dev5..v0.2.1) - 2025-10-12
### Changes:

#### 🚀  Features

- *(health-check)* For stage/prod set disk usages max to 50% - ([6b92356](https://github.com/mapswipe/mapswipe-backend/commit/6b92356539482e614cf826a44e568c7c6b0aaa20))
- *(test)* Add changes on e2e testing for find project - ([31a8ecd](https://github.com/mapswipe/mapswipe-backend/commit/31a8ecd01e3f3a487f8e71e78397883a06303711))
- *(test)* Add e2e testing for export file - ([f465dfc](https://github.com/mapswipe/mapswipe-backend/commit/f465dfcdbb0004258ff0d6c648eaa7aea7313534))

#### 🐛 Bug Fixes

- *(completeness)* Add url_b in completeness project - ([941958b](https://github.com/mapswipe/mapswipe-backend/commit/941958b4fa73472182d9b0281a4612ebf58414c6))
- *(error)* Convert pydantic type to dict recursively in errors - ([78712e7](https://github.com/mapswipe/mapswipe-backend/commit/78712e7d3bd9384740c935fe820fc660a0c9cdcc))
- *(error)* Handle timeout error in background jobs - ([5b9c3f5](https://github.com/mapswipe/mapswipe-backend/commit/5b9c3f54aef52667f42911a5183316fbe0b19a3f))
- *(exports)* Fix exports for find project - ([a386145](https://github.com/mapswipe/mapswipe-backend/commit/a3861458f93b4c0b7572cb9b09a857d7248e63f3))
- *(project)* [**breaking**] Re-use contributors count logic - ([b05f837](https://github.com/mapswipe/mapswipe-backend/commit/b05f83709e0a2f3d4e1b38574553ca12f569bc27))
- *(slack)* Update status of slack progress notification - ([fcd7cd5](https://github.com/mapswipe/mapswipe-backend/commit/fcd7cd5e4c0f33875ec1df44c08fbcb5a91308e0))
- *(street)* Fix timeout issue for street project - ([992105c](https://github.com/mapswipe/mapswipe-backend/commit/992105cf3ec1ff68e553a1d021d606ae2c36456b))
- *(tutorial)* Fix typo in tutorial link - ([d3aec10](https://github.com/mapswipe/mapswipe-backend/commit/d3aec1057aec66c3ef401ed08e9f34e700c38799))
- *(user)* Change slack_user_id to empty string before field change - ([22a70cc](https://github.com/mapswipe/mapswipe-backend/commit/22a70cc825b0929e340d659435bda6cb035b25ef))

#### 🧪 Testing

- *(project)* Skip checking for export if no expected_project_exports_data - ([7586492](https://github.com/mapswipe/mapswipe-backend/commit/7586492701623cc922d244069609d546c51fd1c8))

#### ⚙️ Miscellaneous Tasks

- *(load-data)* Optimization and verbose for mapping data transfer - ([071f032](https://github.com/mapswipe/mapswipe-backend/commit/071f032480d8e84c56965eaeff2d4b2f0edaf967))
- *(submodules)* Update submodules to latest stable - ([2dff549](https://github.com/mapswipe/mapswipe-backend/commit/2dff549677d387f2e681e03ab0d0caea0672f99a))
- *(test)* Update completeness and compare data export files - ([64378f4](https://github.com/mapswipe/mapswipe-backend/commit/64378f4a00f6b9856f38a935ea5363e44f1917bc))
- *(test)* Add project export data for compare and completeness - ([cd274e1](https://github.com/mapswipe/mapswipe-backend/commit/cd274e13a7d727d89cc73ae9380a7f261dfbde7b))

### 🍻 Pull Requests (7)
- (#189) [Fix(user): change slack_user_id to empty string before field change](https://github.com/mapswipe/mapswipe-backend/pull/189)
- (#190) [Feature/e2e testing for exports](https://github.com/mapswipe/mapswipe-backend/pull/190)
- (#191) [Fix(tutorial): fix typo in tutorial link](https://github.com/mapswipe/mapswipe-backend/pull/191)
- (#192) [Handle timeout error in background jobs](https://github.com/mapswipe/mapswipe-backend/pull/192)
- (#193) [Feat/load data optimization](https://github.com/mapswipe/mapswipe-backend/pull/193)
- (#194) [Fix(street): fix timeout issue for street project](https://github.com/mapswipe/mapswipe-backend/pull/194)
- (#195) [Feature/Export testing for Compare. Completeness](https://github.com/mapswipe/mapswipe-backend/pull/195)


## [0.2.1-dev5](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.1-dev4..v0.2.1-dev5) - 2025-10-08
### Changes:

#### 🚀  Features

- *(cron)* Track queue uptime - ([bc64e1b](https://github.com/mapswipe/mapswipe-backend/commit/bc64e1bbf7a639e81745280441984a9c15ec499e))
- *(export)* Add metadata if maxar raster-tiles are used - ([43fdeea](https://github.com/mapswipe/mapswipe-backend/commit/43fdeea974b19e6e6182da831a85eab5d44d183a))
- *(filter)* Add "created by" filter for project and tutorial - ([b60178b](https://github.com/mapswipe/mapswipe-backend/commit/b60178bb80f99680b075883037495a4cdc7a95fa))
- *(firebase)* Update project info on firebase after results is fetched - ([bc62bab](https://github.com/mapswipe/mapswipe-backend/commit/bc62bab95bc04fea02ad5ae36cd83804b898b096))
- *(migration)* Migration project created date - ([ed5a6af](https://github.com/mapswipe/mapswipe-backend/commit/ed5a6af95e220594c242b1612478fb997346acf4))
- *(model)* Add field to save slack message sent bool - ([1ee13fc](https://github.com/mapswipe/mapswipe-backend/commit/1ee13fc8801d40e1fc96da0901aa96f9ec7cade9))
- *(project)* Sync project and contributorCount to firebase on update - ([41444b3](https://github.com/mapswipe/mapswipe-backend/commit/41444b3ff9f3d423ba613a4c3537f204665899dd))
- *(project_type)* Change project type label. - ([6a6299e](https://github.com/mapswipe/mapswipe-backend/commit/6a6299e4ea3b740613a8376132944600f8303532))
- *(pytest)* Add vcr testing configurations - ([ea386b2](https://github.com/mapswipe/mapswipe-backend/commit/ea386b2579bb79c2b8d039546e26e90e4c48d401))
- *(sentry)* Setup support for custom tags - ([80e33ec](https://github.com/mapswipe/mapswipe-backend/commit/80e33ec2a6fe6ae257a1394e53750cad7354e720))
- *(slack)* Handle failure states on project status changes - ([d77d282](https://github.com/mapswipe/mapswipe-backend/commit/d77d2823a000360064bb5c464a144fd6785d7715))
- *(slack)* Remove slack bot name config - ([c00de68](https://github.com/mapswipe/mapswipe-backend/commit/c00de682eba5f3cc6945c8476c08f940ef9932cc))
- *(slack)* Trigger for status change slack message - ([3475408](https://github.com/mapswipe/mapswipe-backend/commit/34754081747d2c831b5bd62aa9b661affc8c3976))
- *(slack)* Change trigger condition for progress change - ([4a720b4](https://github.com/mapswipe/mapswipe-backend/commit/4a720b43faade2c8016ad977755719c060784ab0))
- *(test)* Add e2e testing for validate image project and tutorial - ([795d154](https://github.com/mapswipe/mapswipe-backend/commit/795d154b604118c53c22e571aacd5b7f0054e3f2))
- *(test)* Add e2e data for the street project - ([de2fcce](https://github.com/mapswipe/mapswipe-backend/commit/de2fcce6ecf639485fea314b83999ab7b895179d))
- *(test)* Add e2e testing for validate project and tutorial - ([3ceb302](https://github.com/mapswipe/mapswipe-backend/commit/3ceb302a0e6b5c355aa7cab680e4594dec2c6c38))
- *(test)* Add e2e test for completeness project and tutorial - ([0192d69](https://github.com/mapswipe/mapswipe-backend/commit/0192d69efa91854da1b448a64fc8d522dda40bcf))
- *(test)* Add organization data instead of using factories - ([54d271e](https://github.com/mapswipe/mapswipe-backend/commit/54d271e30dfcfc6c8cdfba6704aaddd025c53e13))
- *(test)* Add e2e testing for the tutorial - ([e4b3518](https://github.com/mapswipe/mapswipe-backend/commit/e4b3518803dac6e4d39c82fc559f62157bdd6703))
- *(test)* Add update test for usergroup. - ([be72a1d](https://github.com/mapswipe/mapswipe-backend/commit/be72a1ddcc36d55351d245c18a703ce13bfa9e72))

#### 🐛 Bug Fixes

- *(export)* Convert progress to float in projects.csv - ([68873c0](https://github.com/mapswipe/mapswipe-backend/commit/68873c0c9cf9cbff594636d92aae357db4b290b5))
- *(export)* Convert progress to float in projects.csv - ([addeff2](https://github.com/mapswipe/mapswipe-backend/commit/addeff2b15f20ceab66b79fedab3db6b6bd6c1ec))
- *(firebase)* Sync maxTasksPerUser on project update - ([5587c75](https://github.com/mapswipe/mapswipe-backend/commit/5587c75214fcdd558c12eea3c339bfc7dfe9a5ba))
- *(firebase)* Fix issue with announcement sync when adding another one - ([0d65429](https://github.com/mapswipe/mapswipe-backend/commit/0d6542999e93056613b1f852f1be7dd537b82f13))
- *(migrations)* Untrack storage config in OverwritableFileField - ([f22d521](https://github.com/mapswipe/mapswipe-backend/commit/f22d52172ac2920552b939f165cb6b602f3565ca))
- *(progress)* Fix project progress - ([81b42cf](https://github.com/mapswipe/mapswipe-backend/commit/81b42cf6d80a317b4b1bad1dec2adff89e04ea59))
- *(project)* Enable editing paused, withdrawn and finished project - ([9558137](https://github.com/mapswipe/mapswipe-backend/commit/95581378038b8b40dba2be4087a5a20be7c32f73))
- *(project)* Add project type on name uniqueness constraint - ([df373bd](https://github.com/mapswipe/mapswipe-backend/commit/df373bdbde3b36a311a237c1c7e4d164c4699e05))
- *(project)* Add validation for project fields - ([0c15e2a](https://github.com/mapswipe/mapswipe-backend/commit/0c15e2a4d67c8212b7a80d0f8de43fdb34aad39e))
- *(project)* Remove default value for "max tasks per user" - ([ad523a1](https://github.com/mapswipe/mapswipe-backend/commit/ad523a14c405bdbd9377792a648be2c3ad534436))
- *(project)* Do not allow editing requesting organization later - ([00d8889](https://github.com/mapswipe/mapswipe-backend/commit/00d888990f67f99d8a7b0adc5770b4167c5c5761))
- *(project)* Throw validation error if required results is empty - ([5bdd864](https://github.com/mapswipe/mapswipe-backend/commit/5bdd864a7073adc56394ab4b493469a162edeab6))
- *(project)* Sort tasks and groups before creating on firebase - ([720af6c](https://github.com/mapswipe/mapswipe-backend/commit/720af6c8f00a81be8ce09385ae671c9425a4d55d))
- *(project)* Update e2e test for street and validate image - ([c7adcc6](https://github.com/mapswipe/mapswipe-backend/commit/c7adcc6762479c28f8f63ffae3475119797645c6))
- *(serializer)* Add unique constraints validation in project serializer - ([529f283](https://github.com/mapswipe/mapswipe-backend/commit/529f2837b4ec8b426dfa9b8c4447372bf2949dab))
- *(serializers)* Add checks for non implemented actions - ([be5a648](https://github.com/mapswipe/mapswipe-backend/commit/be5a648a91d6572dd6b866bd234dae8e393aa197))
- *(test)* Add partial_branches ignore for coverage - ([f1ea57b](https://github.com/mapswipe/mapswipe-backend/commit/f1ea57b4e286aa2ce82516d881f85026c36db734))
- *(test)* Clear out tokens from generated cassette files - ([02bb767](https://github.com/mapswipe/mapswipe-backend/commit/02bb7675a8c296e992c19d761be965c5037be827))
- *(tutorial)* Fix e2e test case for tutorial. - ([15ac780](https://github.com/mapswipe/mapswipe-backend/commit/15ac780824326596ec75bde30235ca3a192e1540))
- *(usergroup-membership)* Filter active membership for count - ([5c0b45c](https://github.com/mapswipe/mapswipe-backend/commit/5c0b45c9cb50ff2b4a6e2fa2a7a43788a7976672))
- *(validate-image)* Use image id for taskId else fallback to index - ([3d3ce15](https://github.com/mapswipe/mapswipe-backend/commit/3d3ce1535e55c13407bd676383433d32a38532fe))

#### 🚜 Refactor

- *(config)* Use Config instead of settings - ([c337f0d](https://github.com/mapswipe/mapswipe-backend/commit/c337f0d3c83c06e5809b06a6a16d7e5399f53037))
- *(loaddata)* Organization migration - ([b4aa130](https://github.com/mapswipe/mapswipe-backend/commit/b4aa130ada9d0d2df9dc1b75ca987d26faaedad8))
- *(project)* Update test to generate name in bulk - ([6623a92](https://github.com/mapswipe/mapswipe-backend/commit/6623a92b86de690eb583fb29d3df9ce20c30887f))

#### 🧪 Testing

- *(project)* Add tests for street project, aggregate, geo functions - ([cb85897](https://github.com/mapswipe/mapswipe-backend/commit/cb85897c410b5fe1cad98bc5a17c0bca401128c5))
- *(project)* Add test for updating processed project - ([9cf46ab](https://github.com/mapswipe/mapswipe-backend/commit/9cf46ab28166ac0aeb98651911078f65db3548e7))
- *(project)* Use different raster tileserver in project mutation tests - ([084b4b3](https://github.com/mapswipe/mapswipe-backend/commit/084b4b3bec9a34bb9001bb3bdce88d315f8aaeac))
- *(project)* Fix failing tests - ([cb7d475](https://github.com/mapswipe/mapswipe-backend/commit/cb7d4759b94da16490098c52ce8928831dd76fc5))
- *(project)* Refactor street, validate and validate image project - ([6d192cf](https://github.com/mapswipe/mapswipe-backend/commit/6d192cfa10f8c3239bec8e61800df101a149f1a5))
- *(project)* Use client_id as firebase_id on test for easy comparison - ([8ff0643](https://github.com/mapswipe/mapswipe-backend/commit/8ff064328dd5bb80adb5e23c857d02b612387ccc))
- *(tutorial)* Add test for image block - ([cec0320](https://github.com/mapswipe/mapswipe-backend/commit/cec03201a28a41203507762ae2602eb8ae01450d))
- *(usergroup)* Fix test for usergroup - ([8d70f60](https://github.com/mapswipe/mapswipe-backend/commit/8d70f607bf6a02acea538f627b17ec50b384a93f))

#### ⚙️ Miscellaneous Tasks

- *(export)* Add trigger for progress change - ([6930913](https://github.com/mapswipe/mapswipe-backend/commit/6930913b59e3262e8a3036cd94bb8de3124ee581))
- *(firebase-cleanup)* Skip cleanup for unknown project results - ([5bf29a0](https://github.com/mapswipe/mapswipe-backend/commit/5bf29a03e2f665bd49a83baa2ab80a52731da47a))
- *(migration)* Use latest parsed project name dataset - ([ffca833](https://github.com/mapswipe/mapswipe-backend/commit/ffca833073341fba4cf21b57f1b0ba9ed4526214))
- *(model)* Add slack user id in admin panel. - ([3cfe3ca](https://github.com/mapswipe/mapswipe-backend/commit/3cfe3ca8fa58f1f1103658b8d1780db30dd14ad2))
- *(model)* Make slack_progress_notification field blankable - ([aab956b](https://github.com/mapswipe/mapswipe-backend/commit/aab956be5754c5ccf2c541f1aec020a206e4ef27))
- *(pre-commit)* Add commitizen - ([f497f71](https://github.com/mapswipe/mapswipe-backend/commit/f497f7111343a075caa719b964b955ffb32b90e1))
- *(project)* Merge migration - ([ea02dc7](https://github.com/mapswipe/mapswipe-backend/commit/ea02dc7251fa98c80ce58624f36f5dfbd1c76044))
- *(project)* Make migration for project type name change - ([254bf8f](https://github.com/mapswipe/mapswipe-backend/commit/254bf8f98273019b1ef4cafe4d0e452d7c3723b9))
- *(project)* Project name fixes - ([af4ee16](https://github.com/mapswipe/mapswipe-backend/commit/af4ee160be32ca1645b44afe37ab98f5390f6e82))
- *(results)* Add test for push result to firebase - ([17edf90](https://github.com/mapswipe/mapswipe-backend/commit/17edf90b0c51053a2e49c294f82f7c6cb20b081a))
- *(s3)* Set media-data as public - ([d6b84bb](https://github.com/mapswipe/mapswipe-backend/commit/d6b84bb8bb21d44f99f07083c3e5f65b3c81b958))
- *(slack)* Update default config in docker and base test - ([c9d4229](https://github.com/mapswipe/mapswipe-backend/commit/c9d4229d5e9d0ebd1fae6a9e900022bc23fa0026))
- *(slack)* Add client for slack not enabled condition - ([cbe2311](https://github.com/mapswipe/mapswipe-backend/commit/cbe2311c36802b9347c1c69ee9166df30689f4dc))
- *(test)* Add firebase test for team. - ([b341f1b](https://github.com/mapswipe/mapswipe-backend/commit/b341f1bb6515548d2e7a5a1b66c5595d503f765a))
- *(test)* Updated the test script for usergroup creation - ([6e52856](https://github.com/mapswipe/mapswipe-backend/commit/6e528560786614a7a26237c2813a77d47a97a069))
- *(test)* Add test for equivalence of generate_name and generate_name_query - ([59d01fb](https://github.com/mapswipe/mapswipe-backend/commit/59d01fb55cd212347980a4de16ca11b76763b875))
- *(test)* Add coverage report exclude list - ([34a4977](https://github.com/mapswipe/mapswipe-backend/commit/34a4977226a81737099fc7c5de757e40d2d7bbe4))
- *(tutorial)* Remove unused create method for tutorial - ([21a0268](https://github.com/mapswipe/mapswipe-backend/commit/21a0268bc6dcf2edc5e0fe932e9fc7db431c30da))
- *(types)* Ignore existing pyright warnings - ([d7e7061](https://github.com/mapswipe/mapswipe-backend/commit/d7e7061dcf120cc3b1f76deeba5e8bceb018b083))

### 🍻 Pull Requests (11)
- (#123) [E2E Test for User Group creation](https://github.com/mapswipe/mapswipe-backend/pull/123)
- (#162) [Add e2e testing for validate and street project and tutorial](https://github.com/mapswipe/mapswipe-backend/pull/162)
- (#168) [E2E BASE: Test for Results, Completeness Project and others](https://github.com/mapswipe/mapswipe-backend/pull/168)
- (#171) [Feat/slack progress message](https://github.com/mapswipe/mapswipe-backend/pull/171)
- (#179) [Add test for equivalence of generate_name and generate_n…](https://github.com/mapswipe/mapswipe-backend/pull/179)
- (#181) [Fix/load data project name](https://github.com/mapswipe/mapswipe-backend/pull/181)
- (#182) [Change project type label.](https://github.com/mapswipe/mapswipe-backend/pull/182)
- (#183) [Ignore existing pyright warnings](https://github.com/mapswipe/mapswipe-backend/pull/183)
- (#185) [Fix(project): throw validation error if required results is empty](https://github.com/mapswipe/mapswipe-backend/pull/185)
- (#186) [Slack status trigger](https://github.com/mapswipe/mapswipe-backend/pull/186)
- (#187) [Feat/membership count issue](https://github.com/mapswipe/mapswipe-backend/pull/187)


## [0.2.1-dev4](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.1-dev3..v0.2.1-dev4) - 2025-09-25
### Changes:

#### 🚀  Features

- *(project)* Support AOI geometry with z values - ([4341f1d](https://github.com/mapswipe/mapswipe-backend/commit/4341f1df83489ff4223bed3bb1709495e8364426))
- *(street)* Add default custom options for street project - ([c7dd323](https://github.com/mapswipe/mapswipe-backend/commit/c7dd3231250a8af8262db16edbea0a60981dbe9f))

#### 🐛 Bug Fixes

- *(filter)* Add prefix on lookup field in unaccented filter - ([0a045e2](https://github.com/mapswipe/mapswipe-backend/commit/0a045e2e3a99f0fd79bf7042c8c2e5e2843c68f5))
- *(project)* Enable firebase sync for archived tutorial - ([4d96b3f](https://github.com/mapswipe/mapswipe-backend/commit/4d96b3f261aaa7464f328d5716a53b32d24b18d2))
- *(project)* Use fallback custom options for export - ([e27cddc](https://github.com/mapswipe/mapswipe-backend/commit/e27cddc9bfc174d6f674adeae0b5d46a008902cc))
- *(validate)* Fix processing of geometry from HOT Tasking Manager - ([814ea5b](https://github.com/mapswipe/mapswipe-backend/commit/814ea5b838bce38e3cfd2ad40776af5a619126b8))

#### ⚙️ Miscellaneous Tasks

- *(helm)* Replace django-app chart with toggle-django-helm - ([920c9e3](https://github.com/mapswipe/mapswipe-backend/commit/920c9e3c2825a3a7edfd5c79f2c444a278451535))
- *(project)* Update error messages for project - ([0a86e21](https://github.com/mapswipe/mapswipe-backend/commit/0a86e21a85a4d686d918ab96caff22811c4c2499))

### 🍻 Pull Requests (1)
- (#180) [Replace django-app chart with toggle-django-helm](https://github.com/mapswipe/mapswipe-backend/pull/180)


## [0.2.1-dev3](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.1-dev2..v0.2.1-dev3) - 2025-09-24
### Changes:

#### 🚀  Features

- *(celery)* Add time limits for project process tasks - ([1fe320b](https://github.com/mapswipe/mapswipe-backend/commit/1fe320b9c72a83e80c39b47a8d80fb255ef3a768))
- *(model)* Add project type to generated name - ([40537b7](https://github.com/mapswipe/mapswipe-backend/commit/40537b7399309cbac8c18331593fa51375e42e8c))
- *(name)* Use common function for name generation in model and name hint - ([312c0ea](https://github.com/mapswipe/mapswipe-backend/commit/312c0ea1d3f220add958dcd0057136fa9c3ad4c0))
- *(project)* Add old_id in project type and filter - ([a4c9a49](https://github.com/mapswipe/mapswipe-backend/commit/a4c9a49a93b4745ddcef9b43b7c4315b84040d77))
- *(query)* New query for generated name hint - ([d2347a0](https://github.com/mapswipe/mapswipe-backend/commit/d2347a00864976354b95a8d5454411ccf66bdd70))
- *(serializer)* Update fire base push conditions - ([6f0c8b4](https://github.com/mapswipe/mapswipe-backend/commit/6f0c8b4a3ec448f1bd9cd564e3b925690fbe25f0))
- *(serializer)* Add validation for tutorial status update - ([f6123a6](https://github.com/mapswipe/mapswipe-backend/commit/f6123a69322a145ba827ca656a6be8ff0732ea44))
- *(test)* Update test to include new generated name - ([2714c5f](https://github.com/mapswipe/mapswipe-backend/commit/2714c5f20ff498cc3d3b1a99b76c56c9840040d2))
- Cleanup temp tables before adding data to temp tables - ([11c76c6](https://github.com/mapswipe/mapswipe-backend/commit/11c76c668fa0c45bdbcb172529c59d31c1568e55))
- Increment the lock expire for pull_results_from_firebase - ([6eeb515](https://github.com/mapswipe/mapswipe-backend/commit/6eeb51546afa1897bb1f6ba0761bfdd893955e8d))
- Add task job expiration - ([b8825e5](https://github.com/mapswipe/mapswipe-backend/commit/b8825e59a21af8de92391e7145f4579a89d9a0ec))

#### 🐛 Bug Fixes

- *(project)* Use valid state machine transition for project - ([54124dd](https://github.com/mapswipe/mapswipe-backend/commit/54124dd47037fe2e5d87e9cc01289a8e88af3c6b))
- *(project)* Update type of old_id - ([0db24d1](https://github.com/mapswipe/mapswipe-backend/commit/0db24d1777b42f2a95f0e20f48e0241a9b1e704f))
- *(project)* Move generate_project_name to project model - ([bb6550d](https://github.com/mapswipe/mapswipe-backend/commit/bb6550d142821bc22bdbaa685c9087e3661d9899))
- *(tutorial)* Use state machine transitions for tutorial - ([cc46de6](https://github.com/mapswipe/mapswipe-backend/commit/cc46de63f418a1f4823a42ee16fd1800c0701947))
- Sync MappingSession app_version max_length with temp table field - ([2bf4743](https://github.com/mapswipe/mapswipe-backend/commit/2bf4743fe517264753f51f0cce574bc28db34748))

#### ⚙️ Miscellaneous Tasks

- *(model)* Remove default value for max_task_per_user - ([8918bce](https://github.com/mapswipe/mapswipe-backend/commit/8918bce2d73285f9ac2c28d981483927fd011a43))
- *(name-query)* Remove project type from name query and test - ([60830d6](https://github.com/mapswipe/mapswipe-backend/commit/60830d66def819a71dd28f22ccabbad12840f974))

### 🍻 Pull Requests (6)
- (#173) [Feat/name query](https://github.com/mapswipe/mapswipe-backend/pull/173)
- (#174) [Feat(serializer): update fire base push conditions](https://github.com/mapswipe/mapswipe-backend/pull/174)
- (#175) [Feat(serializer): add validation for tutorial status update](https://github.com/mapswipe/mapswipe-backend/pull/175)
- (#176) [Fix/worker stuck issue](https://github.com/mapswipe/mapswipe-backend/pull/176)
- (#177) [Feat(celery): Add time limits for project process tasks](https://github.com/mapswipe/mapswipe-backend/pull/177)
- (#178) [Update type of old_id in project model](https://github.com/mapswipe/mapswipe-backend/pull/178)


## [0.2.1-dev2](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.1-dev1..v0.2.1-dev2) - 2025-09-23
### Changes:

#### 🐛 Bug Fixes

- Global file upload issue - ([334f487](https://github.com/mapswipe/mapswipe-backend/commit/334f487d63b50289b1c0c9719a599bf2e1dae202))

### 🍻 Pull Requests (1)
- (#172) [Fix: global file upload issue](https://github.com/mapswipe/mapswipe-backend/pull/172)


## [0.2.1-dev1](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.1-dev0..v0.2.1-dev1) - 2025-09-18
### Changes:

#### 🚀  Features

- *(organization)* Add firebase data validation - ([5d74f82](https://github.com/mapswipe/mapswipe-backend/commit/5d74f82a31bd4eb600c0d3cd8ce4046e3eae96bc))
- *(organization)* Precommit fix - ([54f166a](https://github.com/mapswipe/mapswipe-backend/commit/54f166af0a3658e079cc22e3f1ff311d628038a3))
- *(organization)* E2E test for organization - ([6866ac4](https://github.com/mapswipe/mapswipe-backend/commit/6866ac48f57dd58320e3f06ca5cf6766102e981e))
- *(query)* Add public endpoints for queries - ([a7247e0](https://github.com/mapswipe/mapswipe-backend/commit/a7247e07ad9f0ae79480c697e2de7046c31fef3f))
- *(serializer)* Slack integration for all cases - ([622dd14](https://github.com/mapswipe/mapswipe-backend/commit/622dd14a839651202ce56ca1146b049a4653a93f))
- *(slack)* Add progress bar - ([0f3d59b](https://github.com/mapswipe/mapswipe-backend/commit/0f3d59b30bd0c613c4c663d7459b7e2480ffffb1))
- *(slack)* Dynamic parent message - ([e2b38be](https://github.com/mapswipe/mapswipe-backend/commit/e2b38be3ee3c07b097abb28979e7ce9e1db1dcd5))
- *(slack)* Broadcast thread message to the channel - ([d8621f9](https://github.com/mapswipe/mapswipe-backend/commit/d8621f9749f8727eb12aad0e22f5c08bf8a3bee9))
- *(slack)* Convert all async functions to sync and use celery - ([1b7448d](https://github.com/mapswipe/mapswipe-backend/commit/1b7448dead27b213da27fb6c53f0a1fa1eb345e6))
- *(slack)* Base command for testing slack message - ([7938415](https://github.com/mapswipe/mapswipe-backend/commit/7938415ea9e654de26f904eaab00435e04c0d31d))
- *(slack)* Add function for slack message - ([30a99ad](https://github.com/mapswipe/mapswipe-backend/commit/30a99add7715f98225c59f66cbcf3c465ebc5eb0))
- *(slack)* Setup slack-sdk using webhooks - ([830cc75](https://github.com/mapswipe/mapswipe-backend/commit/830cc7528b68f2da805e44030233b5e464379fc2))
- *(test)* Add dummy slack client in new tests - ([2483ea8](https://github.com/mapswipe/mapswipe-backend/commit/2483ea8403ed57aab4c39d9766ed7832b88ad693))
- *(test)* Add dummy slack client in mutation test - ([ccd8997](https://github.com/mapswipe/mapswipe-backend/commit/ccd89976dd343658b31509ab1717336ff9018cc6))

#### 🐛 Bug Fixes

- *(model)* Overwrite get_prep_value to remove empty string - ([58f2719](https://github.com/mapswipe/mapswipe-backend/commit/58f27193b6d8e2bf0b779c2d4bc3618deffef807))
- *(slack)* Remove calls to slack tasks and update migrations - ([a569bc9](https://github.com/mapswipe/mapswipe-backend/commit/a569bc99aa687c47e365267ca6126c563f4f4d26))

#### 🚜 Refactor

- *(serializer)* Combine logic and cleanup - ([da1f064](https://github.com/mapswipe/mapswipe-backend/commit/da1f064e983a04ce6fed3b54e6851f4bb81213d2))
- *(slack)* Implement final design changes - ([8f1bedd](https://github.com/mapswipe/mapswipe-backend/commit/8f1bedd1fcc82f8b973b96ba0eb62bafc12afeb3))
- *(tasks)* Separate tasks and messages - ([11b6c07](https://github.com/mapswipe/mapswipe-backend/commit/11b6c0761987244917e260eb9916def641626241))

#### ⚙️ Miscellaneous Tasks

- *(model)* Add slack_user_id and slack_thread_ts fields. - ([922a24d](https://github.com/mapswipe/mapswipe-backend/commit/922a24d1e0857272e7540e468028c3c67eab5246))
- *(organization)* Update assets on organization - ([8665fe8](https://github.com/mapswipe/mapswipe-backend/commit/8665fe89fed7259f7f210479434decf36ca74ac5))
- *(slack)* Accept None type for tutorial_id and cover_image - ([c0d3f60](https://github.com/mapswipe/mapswipe-backend/commit/c0d3f6095a487676d2f8ddbc222ff283b8814d65))
- *(slack)* Base setup for slack webclient - ([3968127](https://github.com/mapswipe/mapswipe-backend/commit/3968127750939eb06ef9f4abacf8f6b01cf6b4be))
- *(test)* Test commands for all cases - ([5ecd5e7](https://github.com/mapswipe/mapswipe-backend/commit/5ecd5e77277662899a097190657e3ca755c91462))

### 🍻 Pull Requests (4)
- (#122) [E2E Test for Organization](https://github.com/mapswipe/mapswipe-backend/pull/122)
- (#134) [Feat/slack phase ii](https://github.com/mapswipe/mapswipe-backend/pull/134)
- (#169) [Fix(model): overwrite get_prep_value to remove empty string](https://github.com/mapswipe/mapswipe-backend/pull/169)
- (#170) [Feat(query): add public endpoints for queries](https://github.com/mapswipe/mapswipe-backend/pull/170)


## [0.2.1-dev0](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.0-dev9..v0.2.1-dev0) - 2025-09-11
### Changes:

#### 🚀  Features

- *(db)* Fixes - ([2330dfa](https://github.com/mapswipe/mapswipe-backend/commit/2330dfa5584f58e7cb0d0331d8a6c65192ad904d))
- *(enums)* Add firebase status enum to the list - ([b60f589](https://github.com/mapswipe/mapswipe-backend/commit/b60f58988c9eb3f271bccd2ba2f6c4f8c018b601))
- *(export)* Enable generation of project geom - ([0b42a70](https://github.com/mapswipe/mapswipe-backend/commit/0b42a70b48e633090b3ff716523cc5ecd2123c68))
- *(project)* Exclude actual geometry from graphql - ([3d9ac2a](https://github.com/mapswipe/mapswipe-backend/commit/3d9ac2ada74992b74b7a834cd04f354cdb13180b))
- *(project)* Add one-on-one mapping from project to geometry - ([aeda988](https://github.com/mapswipe/mapswipe-backend/commit/aeda9888a1e15fdcde5464debfbda80c98e52476))
- *(project)* Add new project status and renamed existing - ([26f5a7b](https://github.com/mapswipe/mapswipe-backend/commit/26f5a7b902932f126f3899eabf07dd9dfffcbb0d))
- *(project)* Add is_featured on project processed mutation - ([a717c05](https://github.com/mapswipe/mapswipe-backend/commit/a717c056286f37eec9e9d57805fea13f2c0db2b1))
- *(project)* Add status_message for capturing errors for background tasks - ([1220178](https://github.com/mapswipe/mapswipe-backend/commit/12201782ab3eedfdfcec5d85141c91cb2cb9b32d))
- *(project)* Add new project status and renamed existing - ([6c62b69](https://github.com/mapswipe/mapswipe-backend/commit/6c62b693befda8ed7d6a59576ec4883e4bd4f3f8))
- *(street)* Add AOI area validation - ([ba25894](https://github.com/mapswipe/mapswipe-backend/commit/ba258949d7ceaac016c0cdf8f47986259662344f))
- *(street)* Add tutorial task property for the street project - ([b806244](https://github.com/mapswipe/mapswipe-backend/commit/b8062444acdcf755dd1e4fd481b76106e7acc68e))
- *(street)* Street tutorial task generation - ([276665b](https://github.com/mapswipe/mapswipe-backend/commit/276665bd4c4a71a4e1eee3359892cf4670c55153))
- *(tutorial)* Add new tutorial status - ([e0ca4e5](https://github.com/mapswipe/mapswipe-backend/commit/e0ca4e5d1f3e6d97634069b30887bba177b5bd12))
- *(validate)* Save aoi geometry for all validate type projects - ([cd719fa](https://github.com/mapswipe/mapswipe-backend/commit/cd719fabe0dcd509ab55c12e9f95f560d72726b8))
- *(validate-image)* Mark input assets as deleted if not required - ([4832af0](https://github.com/mapswipe/mapswipe-backend/commit/4832af08fe0a82b817f805eb67c1551cce2e1908))
- Include existing data for existing project migration - ([5425669](https://github.com/mapswipe/mapswipe-backend/commit/54256696cf03e3f334e48432bdaf609439a3040d))
- Add script for running in non-dev environment - ([179e32f](https://github.com/mapswipe/mapswipe-backend/commit/179e32f8747c2137eb3d82a5b7292206cc0a3d5a))

#### 🐛 Bug Fixes

- *(project)* Error logging for background process - ([4ef2a40](https://github.com/mapswipe/mapswipe-backend/commit/4ef2a4092dabf214a84c519f87255a3ac6e1a351))
- *(project)* Use gettext for validation errors - ([908d0b1](https://github.com/mapswipe/mapswipe-backend/commit/908d0b1b5d0bf948d723150bfc54ea1f2993fc1d))
- *(project)* Set bbox, centorid and area in project for the time being - ([c372df7](https://github.com/mapswipe/mapswipe-backend/commit/c372df7d645655474f3edbbde372f9b3061f24b0))
- *(project)* Only validate for project_instructionwhen publishing a project - ([4b84405](https://github.com/mapswipe/mapswipe-backend/commit/4b8440596cea92148a9222da2712b78cbd401a06))

#### 🚜 Refactor

- *(geo)* Create utilities for geo transformation - ([bd2db06](https://github.com/mapswipe/mapswipe-backend/commit/bd2db066e0d02f2b2e780693b786e42ce64a5b58))
- *(project)* Prefix pydantic and shapely types - ([0fb1f89](https://github.com/mapswipe/mapswipe-backend/commit/0fb1f897ae04455c4c7db9de963275c98ee4b160))

#### 🧪 Testing

- *(tutorial)* Fix tests for tutorial and project - ([e8ab4af](https://github.com/mapswipe/mapswipe-backend/commit/e8ab4af4a29900f13f82de732fcc9cf80fe0d257))

#### ⚙️ Miscellaneous Tasks

- *(comments)* Add/remove comments - ([6704ea3](https://github.com/mapswipe/mapswipe-backend/commit/6704ea340bd9571e7cf4c80a4d4d915d58d1c7c9))
- *(migrations)* [**breaking**] Force squash migrations - ([de159e6](https://github.com/mapswipe/mapswipe-backend/commit/de159e66a7e342c8029384ee9e3462edb8529d96))
- *(pydantic)* Update description for custom pydantic defs - ([15d6b31](https://github.com/mapswipe/mapswipe-backend/commit/15d6b31613a38d44c7f3880cf00a0c197b9a8275))

### 🍻 Pull Requests (8)
- (#149) [Feat(street): Street tutorial task generation](https://github.com/mapswipe/mapswipe-backend/pull/149)
- (#157) [Only validate for project_instruction when publishing project](https://github.com/mapswipe/mapswipe-backend/pull/157)
- (#158) [Add new project status and renamed existing](https://github.com/mapswipe/mapswipe-backend/pull/158)
- (#160) [Feat/pre deployment setup](https://github.com/mapswipe/mapswipe-backend/pull/160)
- (#161) [Add one-on-one mapping from project to geometry](https://github.com/mapswipe/mapswipe-backend/pull/161)
- (#163) [Asset generations for project types](https://github.com/mapswipe/mapswipe-backend/pull/163)
- (#164) [Feat(enums): add firebase status enum to the list](https://github.com/mapswipe/mapswipe-backend/pull/164)
- (#165) [Error logging for background process](https://github.com/mapswipe/mapswipe-backend/pull/165)


## [0.2.0-dev9](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.0-dev8..v0.2.0-dev9) - 2025-09-07
### Changes:

#### 🚀  Features

- *(project)* Re-calculate area on project from task group - ([d70e186](https://github.com/mapswipe/mapswipe-backend/commit/d70e1864ec05628c9b0601a5d22f0d22d32f37b3))
- *(project)* Calculate geo info for projects - ([15550d0](https://github.com/mapswipe/mapswipe-backend/commit/15550d070819d68ef6fdbb656eb122fae1340219))
- Add project progress status - ([d28db85](https://github.com/mapswipe/mapswipe-backend/commit/d28db856d067f72f8df2f3e3d3ab273ece4fb425))
- Add globalExportAsset - ([cf49ba9](https://github.com/mapswipe/mapswipe-backend/commit/cf49ba9e51cfbf45338305932780fe91e71d0712))
- Add project contribution progress stats - ([8a450dc](https://github.com/mapswipe/mapswipe-backend/commit/8a450dcd9790c96ab81f457c9cbd855655d8077f))

#### 🐛 Bug Fixes

- *(announcement)* Use correct firebase uri for announcement - ([84067c0](https://github.com/mapswipe/mapswipe-backend/commit/84067c091f66c5b4671d891719691913a79ccc76))
- *(asset)* Area calculation for aoi assets - ([e4de22f](https://github.com/mapswipe/mapswipe-backend/commit/e4de22f30d9f39c0ad6bc6bc711c989bcd73914d))
- *(asset)* Fix validation for bbox - ([b6726f6](https://github.com/mapswipe/mapswipe-backend/commit/b6726f60a6fd3cdb22bec6a85995721b78a6a3a8))
- *(project)* Fix query for directly uploaded image object assets - ([ab5a713](https://github.com/mapswipe/mapswipe-backend/commit/ab5a7135f895985f11f0731f97a3740badaa1c5a))
- *(project)* Validate image asset type specifics issue - ([4b3bcbb](https://github.com/mapswipe/mapswipe-backend/commit/4b3bcbb9e0e9166ca4442af35cfc0608d88a2f32))
- *(project)* Use enum label on error message instead of enum value - ([be08f15](https://github.com/mapswipe/mapswipe-backend/commit/be08f15c63f457f4b3efd673d3798ffaea740708))
- *(project)* Convert to geography before calculating group area - ([a759caf](https://github.com/mapswipe/mapswipe-backend/commit/a759cafb0e704041395be82de73f1bdbccd6301e))
- *(project)* Set progress status when progress is 100 - ([ea71f53](https://github.com/mapswipe/mapswipe-backend/commit/ea71f537082940518c4e3c95e0b829ca27930393))

#### 🧪 Testing

- *(project)* Merge e2e test for compare and find - ([f407238](https://github.com/mapswipe/mapswipe-backend/commit/f407238aa737b44508e5c82fd4929ac0047b7d90))
- *(project)* Add test files for compare project type - ([d4474b3](https://github.com/mapswipe/mapswipe-backend/commit/d4474b3d7eac590abe17c0cc54517af5caa9fce6))
- *(project)* Use new status api - ([349dfbb](https://github.com/mapswipe/mapswipe-backend/commit/349dfbb697140ffc2a412e62f63f34bb3adad056))
- *(project)* Create test script for project creation - ([bb1ee6b](https://github.com/mapswipe/mapswipe-backend/commit/bb1ee6b50865ed37a081b18f4d43e9db250d3b3d))
- *(validate)* Update tests with more real examples - ([08b28e0](https://github.com/mapswipe/mapswipe-backend/commit/08b28e04f8297742810abac67e7fb03def812bc6))

#### ⚙️ Miscellaneous Tasks

- *(announcement)* Add announcement - ([09bf774](https://github.com/mapswipe/mapswipe-backend/commit/09bf774353cb31ab315e8700a01a23575911af98))
- *(migration)* Create merge migration - ([f0c25ab](https://github.com/mapswipe/mapswipe-backend/commit/f0c25abc735a709390bdaa4f42e64cb3a49ae95f))
- *(script)* Add a script to run common checks - ([7f07402](https://github.com/mapswipe/mapswipe-backend/commit/7f07402f5bc40e64f86c91a35fd0960314c96f4f))
- *(test)* Add additional tests - ([8c8a4a4](https://github.com/mapswipe/mapswipe-backend/commit/8c8a4a4b701d46caaf56cfdc6a5763a4bd76c7b2))

### 🍻 Pull Requests (6)
- (#107) [Add additional tests](https://github.com/mapswipe/mapswipe-backend/pull/107)
- (#146) [Add announcement](https://github.com/mapswipe/mapswipe-backend/pull/146)
- (#148) [E2E test for Project creation ](https://github.com/mapswipe/mapswipe-backend/pull/148)
- (#151) [Feat: add project contribution progress stats](https://github.com/mapswipe/mapswipe-backend/pull/151)
- (#153) [Calculate geo info for projects](https://github.com/mapswipe/mapswipe-backend/pull/153)
- (#155) [Fix(project): Validate image asset type specifics issue](https://github.com/mapswipe/mapswipe-backend/pull/155)


## [0.2.0-dev8](https://github.com/mapswipe/mapswipe-backend/compare/v0.2.0-dev7..v0.2.0-dev8) - 2025-09-05
### Changes:

#### 🚀  Features

- *(project)* Add project_type_specific_output_asset to project - ([47247e6](https://github.com/mapswipe/mapswipe-backend/commit/47247e6b0bc6caa2e738b5b282f921f4f0cde92f))

#### 🐛 Bug Fixes

- *(project)* Update aoi geometry area - ([069d665](https://github.com/mapswipe/mapswipe-backend/commit/069d665e7057d325b4d7098376d5c2bed8184ec6))
- *(project)* Rename project_type_specific_output to project_type_specific_output_asset - ([49c90f4](https://github.com/mapswipe/mapswipe-backend/commit/49c90f464935bd92f8392e0bc261c7fd4c79fbf8))
- *(project-migration)* Update project migration 25 to update asset id - ([60cf2c6](https://github.com/mapswipe/mapswipe-backend/commit/60cf2c635aa10be0746b6ab2391735b859d7eef8))

#### ⚙️ Miscellaneous Tasks

- *(submodule)* Update assets url to use ssh - ([d1fd46d](https://github.com/mapswipe/mapswipe-backend/commit/d1fd46da68059d9feb6ab1df09a016fdd70f34b1))

### 🍻 Pull Requests (3)
- (#150) [Attach AOI geometry to project](https://github.com/mapswipe/mapswipe-backend/pull/150)
- (#152) [Update project migration 25 to update asset id](https://github.com/mapswipe/mapswipe-backend/pull/152)
- (#154) [Update aoi geometry area](https://github.com/mapswipe/mapswipe-backend/pull/154)


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
