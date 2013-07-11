---
layout: jp_post
title: Q. 起動・停止・再起動等の操作実行がタイムアウトで失敗します。対処方法はありますか？
category: jp
---

## 回答

HyClopsでは起動・停止・再起動等の処理をZabbixの標準機能であるGlobalScriptを活用しています。  
ZabbixのGlobalScriptはZabbixフロントエンドが実行します。
そのため、Zabbixフロントエンドの中のスクリプト実行に関するタイムアウト設定を変更することで対応が可能となります。

変更箇所は以下です。

Zabbixフロントエンドディレクトリ/include/defines.inc.php

    define('ZBX_SCRIPT_TIMEOUT',            60); // in seconds

デフォルトでは60秒に設定されています。
どうしてもタイムアウトが発生してしまう場合にはここの値を調整します。

