---
layout: post
title: Q. Is it possible to access AWS API via an HTTP proxy?
category: en
---

## Answer

It is possible to configure the following.

### 1: Set proxy information

Set proxy information to environment variable or hyclops.conf

- http_proxy : proxy setting for communication of http
- https_proxy : proxy setting for communication of https
- no_proxy : proxy setting for excluded network

In case of setting in hyclops.conf

    [environments]
    http_proxy = http://username:password@proxy.example.com:8080
    https_proxy = http://username:password@proxy.example.com:8080
    no_proxy = "localhost,127.0.0.1,10.1.1.*"

### 2: Add code in libcloud for reading proxy settings

Add code in libcloud/common/base.py(in "apache-libcloud" python package).

    import os    # add
    import base64   # add
    def connect
    ...
    ### begin to add
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
    ### end to add
        self.connetion = connection

### Note

If your systems python version is 2.6, you cannot use authentication proxy.
If you use the proxy of no authentication, you have to set the following settings.

Set in libcloud/common/base.py(in "apache-libcloud" python package).

    def connect
    ...
        connection = self.conn_classes[False]("proxy hostname", proxy port number)   # <=Add proxy settings option
