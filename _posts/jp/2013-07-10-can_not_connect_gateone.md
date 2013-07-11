---
layout: jp_post
title: Q. GateOneに接続できません原因として何が考えられますか？
category: jp
---

## 回答

以下の原因が考えられます。
状況を確認し対応して下さい。  

<ul>
<li> セキュリティ証明書の問題</li>
<li> 接続元サーバ(Zabbix Server)とGateOneサーバの時刻ズレの問題</li>
<li> APIキー設定の問題</li>
<li> 接続元許可設定の問題</li>
</ul>

### セキュリティ証明書の問題

セキュリティ証明書が信頼できない場合、ZabbixダッシュボードからSSH接続を実行しても画面に何も表示されません。
GateOneサーバに信頼できるセキュリティ証明書を登録するか、例外として事前に登録しておく必要があります。

### 接続元サーバ(Zabbix Server)とGateOneサーバの時刻ズレの問題

GateOneでは認証用トークン生成及び認証チェックに時刻情報を利用しています。
そのため、認証用トークンを生成する接続元(Zabbix Server)の時刻とチェックを実行するGateOneサーバで時刻がずれている場合に不正なトークンであるとみなされ接続が拒否されます。

この時、GateOneのログ(/opt/gateone/logs/webserver.log)に以下の内容が書きこまれます。

    API authentication failed due to an expired auth object.
    If you just restarted the server this is normal (users just need to reload the page).
    If  this problem persists it could be a problem with the server's clock (either this server or the server(s) embedding Gate One).

接続元とGateOneサーバの時刻を正しく設定して下さい。

### APIキー設定の問題

/opt/gateone/server.confのapi_keys設定に書かれているAPIキー及びシークレットキーが正しくZabbixのマクロに設定されているかを確認して下さい。
Zabbix側では次の2つのグローバルマクロで設定を行います。  
{$GATEONE_KEY},{$GATEONE_SECRET}

APIキーの設定が誤っている場合、GateOneのログに以下の内容が書きこまれます。

    Error running plugin WebSocket action: ssh_get_connect_string

APIキーの設定を見なおして下さい。

### 接続元許可設定の問題

GateOneは接続元の許可設定を行う機能があります。
接続元許可設定は、/opt/gateone/server.confのoriginsで設定します。
Zabbixサーバからの接続許可設定が正しく行われているか確認して下さい。

接続元許可設定が正しく実施されていない場合、GateOneのログに以下の内容が書きこまれます。

    Access denied for origin: http://zabbix-server-hostname

上記エラー発生の場合には、server.confに以下の設定を実施します。

    origins = "http://zabbix-server-hostname"

設定変更後、GateOneを再起動して下さい。

