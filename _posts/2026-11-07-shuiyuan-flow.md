---
layout: post
title: "源流 Shuiyuan Flow：开源一个 Flutter 五端论坛客户端 MVP"
subtitle: "从离线浏览到原生桌面验证，记录当前交付与下一步"
description: "参考 fluxdo 的跨平台思路，完成源流离线 MVP，并公开 Android、Windows、Linux 的验证结果与未完成事项。"
date: 2026-11-07 00:00:00 +0800
author: determine
tags: [Flutter, 开源项目, 工程实践]
---

最近，我把 **源流 · Shuiyuan Flow** 开源了。它是面向上海交通大学水源社区的非官方 Flutter 客户端探索，目标覆盖 Android、iOS、Windows、macOS 和 Linux，希望让手机阅读和桌面浏览都更自然。

[查看 GitHub 源码与运行说明 →](https://github.com/determine123/shuiyuan-flow)

目前发布的是**离线 MVP 源码**。演示话题均为虚构，默认不会连接真实社区；五端工程已经包含在仓库里，但各平台的验证进度并不相同。

## 为什么参考 fluxdo

[Lingyan000/fluxdo](https://github.com/Lingyan000/fluxdo) 提供了 Flutter 跨平台 Discourse 客户端的参考。源流借鉴它的五端工程组织、自适应界面与网络层分层思路，固定参考提交为 `bc5a04b0fc09bde915415e2ab345bc24c8c8146c`。

源流独立实现了一组轻量核心功能，没有完整移植 fluxdo，也没有引入上游的 Rust 代理、Linux.do 积分系统或 Cloudflare 绕过逻辑。仓库保留来源说明，采用 GPL-3.0 许可证。

参考的重点是产品如何围绕“阅读”组织：手机与桌面共享核心流程，同时保留适合各自屏幕的导航。FluxDO 面向 Linux.do，源流面向水源，两者的账号配置、接口约束、实现范围和安装包都需要分别看待。

## 从产品目标到当前实现

源流希望提供流畅、优雅的论坛浏览体验。具体落点是让查找话题、连续阅读、收藏内容和保存草稿更顺手，并让这些操作在窄屏与宽窗口之间保持一致。

这里的“流畅”仍是需要验证的目标。默认测试通过、桌面原生启动成功，分别证明对应流程可运行，不能代替真机帧耗时、图片密集内容和长时间使用的测试。

## 这一版已经能做什么

界面采用 Material 3：手机使用底部导航，宽窗口使用侧栏，支持浅色、深色与跟随系统主题。阅读流程包含话题列表、分类、搜索、分页、HTML 帖子展示，以及长话题分批加载。

收藏和草稿保存在本机，编辑时有返回保护；真实账号与演示数据按范围分开保存。网络层已经提供 Discourse User API 的读取、创建话题、回复和点赞适配，凭据使用系统安全存储，但这些真实接口尚未与水源站方联调。

## 技术实现与上游能力边界

源流当前使用 Flutter / Dart 与 Material 3 构建界面，通过 ChangeNotifier 管理状态，使用 `http` 访问接口、`flutter_widget_from_html_core` 展示帖子，分别以 SharedPreferences 和系统安全存储保存本地内容与凭据。`ForumRepository` 将演示数据和真实接口隔离，方便在没有社区访问条件时验证交互。

对照 [fluxdo 的功能说明](https://github.com/Lingyan000/fluxdo#特性)，还应区分三个层次：

- **已实现的离线流程**：话题浏览、分类搜索、HTML 阅读、本地收藏、草稿与主题。
- **已有适配但未真实联调的接口**：用户识别、话题读取、发帖回复和点赞。
- **仍未完成的扩展能力**：图片上传、投票、徽章、通知和完整浏览器授权。

源流的楼层分批请求不等于上游的 HTML 分块渲染，也没有继承上游专用图片缓存、MessageBus 通知或 Rust 网络代理。上游的 Riverpod、Dio 等技术栈不能直接写成源流的实现说明。

## 验证到了哪一步

- **Android**：Debug APK 已在 Android 15 模拟器完成安装、启动和本地数据持久化验证。当前没有可用真机，尚未完成真机 Profile 测试。
- **Windows**：Release 编译成功，原生集成测试通过；Release 窗口完成了启动、实际按键搜索和 Tab 焦点检查。
- **Linux**：Release 编译成功，原生集成测试通过；在 WSLg 中验证了中文显示、鼠标、滚轮，以及宽窗口切换为窄窗口导航的行为。这个环境使用软件渲染，不能代表独立 Linux 电脑的性能。
- **iOS / macOS**：已包含工程，尚未在对应宿主及设备上验证。

默认单元与组件测试共 **28 项通过**。这些结果说明部分核心流程已经跑通，还不足以证明所有设备和场景都流畅。仓库中另外保留了专门重现浏览缺陷的验收用例，当前仍有两项已知问题：切换标签后列表位置丢失，以及搜索失败时旧结果仍然显示。

详细证据和限制见 [Android 验证记录](https://github.com/determine123/shuiyuan-flow/blob/main/docs/VERIFICATION.md)、[原生桌面验证](https://github.com/determine123/shuiyuan-flow/blob/main/docs/NATIVE_VALIDATION.md) 和 [浏览体验审计](https://github.com/determine123/shuiyuan-flow/blob/main/docs/BROWSING_EXPERIENCE_AUDIT.md)。

## 真实社区接入还需要什么

源流不是水源社区或上海交通大学的官方产品。根据[水源社区协议](https://shuiyuan.sjtu.edu.cn/tos)，第三方客户端访问社区需要书面许可；目前尚未取得该许可，真实接入开关保持关闭。

后续需要先确认许可范围、站方 User API 配置和用户授权，再验证真实登录与阅读。当前授权入口仅支持手动填写用户级密钥和 Client ID，尚未实现 jAccount 浏览器授权回调。图片上传、投票、徽章、私信与实时推送也还没有完成。

## 接下来继续做

优先修复已知浏览问题，完善浏览器授权流程，并在条件具备后执行 Android 真机 Profile 与 Apple 平台验证。真机性能评估会按 [Flutter 官方方法](https://docs.flutter.dev/perf/ui-performance)使用 Profile 模式，保留设备条件与时间线，不把模拟器 Debug 数据当成真机性能结论。

如果想阅读实现，可以从 `lib/forum_api.dart` 的接口适配、`lib/app_state.dart` 的本地状态，再到 `lib/main.dart` 的自适应界面开始。构建与测试命令、已知限制以及贡献方式都放在[仓库 README](https://github.com/determine123/shuiyuan-flow#readme)中。

## 获取与参与

目前可以从 GitHub 获取源码并运行离线演示，仓库尚未发布 Release 安装附件。FluxDO 的安装包和 AltStore 源属于上游项目，不能用来安装源流。

欢迎在[源流 Issues](https://github.com/determine123/shuiyuan-flow/issues)反馈问题，附上平台、版本、复现步骤与实际结果。请先移除日志和截图中的凭据与个人内容。后续会优先完善阅读体验与测试证据，再根据社区许可和接口条件扩展功能。
