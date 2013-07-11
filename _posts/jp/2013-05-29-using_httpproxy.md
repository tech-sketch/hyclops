---
layout: jp_post
title: Q. HTTPプロキシ経由でAWS APIにアクセスすることは可能ですか？
category: jp
---

## 回答

以下の設定を行うことにより対応可能です。

### 1: 環境変数またはhyclops.confにプロキシ設定を行う

環境変数またはhyclops.confのenvironmentsにプロキシ情報を設定します。

* http_proxy : http通信に利用するプロキシ設定
* https_proxy : https通信に利用するプロキシ設定
* no_proxy : プロキシ経由で通信しないネットワークアドレス設定

hyclops.confに設定する場合は以下のように設定します。

    [environments]
    http_proxy = http://username:password@proxy.example.com:8080
    https_proxy = http://username:password@proxy.example.com:8080
    no_proxy = "localhost,127.0.0.1,10.1.1.*"

### 2: libcloudにプロキシ設定読み込み処理を追記

設定を書き込むファイルは"apache-libcloud"Pythonパッケージのlibcloud/common/base.pyです。

    import os    # 追加
    import base64   # 追加
    def connect
    ...略
    ### ここから
        proxy_env = "https_proxy" if port == 443 else "http_proxy"
        proxy_url = os.environ.get(proxy_env)
        if proxy_url:
            proxy = urlparse.urlparse(proxy_url)
            if proxy.hostname and proxy.port:
                if port == 443:
                    connection = self.conn_classes[secure](proxy.hostname, proxy.port)
                    if proxy.username and proxy.password:
                        headers = kwargs.get('headers', []) 
                        headers = {"Proxy-Authorization":"Basic " + base64.b64encode(proxy.username + ":" + proxy.password)}
                        kwargs["headers"] = headers
                    connection.set_tunnel(**kwargs)
                else:
                    connection = self.conn_classes[False](proxy.hostname, proxy.port)
    ### ここまで
        self.connetion = connection

### 注意

Python2.6系を利用している場合、認証有りプロキシが利用できません。
認証無しのプロキシを利用する場合は、以下の設定で対応できます。

設定するファイルは"apache-libcloud"Pythonパッケージのlibcloud/common/base.pyです。

    def connect
    ...略
        connection = self.conn_classes[False]("proxy hostname", proxy port number)   # <=proxy設定を引数に追加

