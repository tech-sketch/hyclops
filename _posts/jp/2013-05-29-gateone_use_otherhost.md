---
layout: jp_post
title: Q. AmazonEC2インスタンスやvSphere仮想マシン以外のホストに対してGateOneでSSH接続は可能ですか？
category: jp
---

## 回答

Zabbixのマップ機能およびURL設定機能を用いることで可能です。  
方法は以下の通りです。

### 1: マップ作成  

接続したいホストがマップ上に表示されるよう作成します。  
マップの作成はZabbix管理画面の「設定」->「マップ」->「マップの作成」から実施します。
作成したマップにマップアイコンとして、タイプ「ホスト」または「ホストグループ」のアイコンを設置します。

### 2: マップアイコンにGateOneに接続するためのURLを設定  

マップアイコンにGateOneのアクセスURLを登録します。
HyClopsが用意しているGateOne接続用ページ(gateone.php)にホストIDをパラメータとして渡すことでSSH接続が実現できます。
マップアイコンに登録できるURLにはZabbixマクロが利用可能であるため、以下のようにURLを設定します。

    http://zabbix-server-hostname/zabbix/gateone.php?hostid={HOST.ID}

### 3: マップ上のアイコンを選択し、GateOne接続URLをクリック  

接続するにはマップを表示し、接続したいターゲットホストをクリックします。
表示されるメニューの中からGateOne接続URLをクリックすることで接続できます。
