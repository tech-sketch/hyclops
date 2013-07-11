---
layout: jp_post
title: Q. 稼働するESXiホスト毎に仮想マシンをホストグループ登録は可能ですか？
category: jp
---

## 回答

HyClopsでは仮想マシンの登録時にマクロの情報をチェックし、ホストグループへの自動登録を実現しています。
登録するホストグループは{$VM_GROUPS}マクロの設定情報をもとに実施されます。
vSphereESXiテンプレートにはデフォルトでこのマクロが以下のように設定されています。

    {$VM_GROUPS} => vSphereVM

このマクロ設定をvSphereESXi用Zabbixホストのホストマクロで更新します。
以下のように設定することでホスト名のグループにも自動的に登録されます。

    {$VM_GROUPS} => vSphereVM,ホスト名({HOST.HOST}等のマクロ展開には未対応)

注意: デフォルトで設定されているvSphereVMを記述するのを忘れないで下さい。

