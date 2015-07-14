# 概要 {#about}

HyClopsはZabbixの拡張ツールです。
Amazon EC2やVMware vSphereの環境を統合的にZabbix上で管理することを実現します。

我々の目標は、物理環境、プライベート仮想環境、パブリッククラウド環境を含めたハイブリッドな環境を統合して管理できるようにすることです。
さらに、統合するだけでなく、可能な限り自動化、自律化を推進し、運用者が煩わしい作業を行うことなくサービス運用を実現できるよう取り組んでいます。

その第1ステップとして、統合監視ツールであるZabbixを拡張し、ハイブリッド環境の監視や簡単な操作をZabbixから実現できるようにしました。
現在対応している環境は、AWSおよびvSphereのみでありますが、必要に応じて追加できる仕組みを導入しています。

HyClopsでは外部スクリプトやZabbix senderおよびメッセージキューイングシステムを活用しています。

HyClopsの機能概要:

- EC2インスタンスやvSphere仮想マシン情報をZabbixに自動登録
- Zabbixエージェントレスでインスタンスの情報を自動監視(AWS APIおよびvSphere APIを利用)
- Zabbixグローバルスクリプトを用いてインスタンスの起動/停止処理を実行
- Zabbixダッシュボード拡張によるEC2インスタンス、vSphere仮想マシン情報の一覧表示
- (オプション機能) [GateOne](https://github.com/liftoff/GateOne)-Zabbix連携によるZabbixダッシュボードからのSSHコンソール接続

# リリースノート {#releases}

<ul>
  <li> 2013/12/12 ver.0.2.0
    <ul>
      <li> Zabbix 2.2への対応を実施</li>
      <li> プラットフォームが取得できない(unknown)EC2インスタンスへのテンプレート割り当てロジック変更</li>
      <li> ダッシュボードのvSphere情報表示パネルにインタフェース表示カラムを追加</li>
    </ul>
  </li>
  <li> 2013/07/12 ver.0.1.0
    <ul>
      <li> Amazon EC2およびVMware vSphere ESXi管理への対応</li>
      <li> インスタンス情報の自動登録対応</li>
      <li> 複数インスタンスへの起動/停止/再起動コマンド実行対応</li>
      <li> Webブラウザ上でのSSHコンソール接続対応</li>
    </ul>
  </li>
</ul>
 
# アーキテクチャ {#architecture}

![architecture]({{ site.production_url }}/assets/images/HyClops_architecture.png)

HyClopsは3つのコンポーネントで構成されています。

## Zabbix Serverコンポーネント

Zabbix Serverコンポーネントの役割は以下の通りです。

<ul>
  <li> インスタンス情報にダイレクトにアクセスするため、オリジナルのZabbixダッシュボードを置き換え</li>
  <li> 外部スクリプト機能を利用し、定期的に各環境の情報取得リクエストを送付</li>
  <li> グローバルスクリプト機能を利用し、各環境のインスタンス操作実行リクエストを送付</li>
</ul>

## メッセージキューイング処理コンポーネント

メッセージキューイング処理コンポーネントの役割は以下の通りです。

- キューイングプロセスをTCPポートで待受 ( MQにはZeroMQを使用 ) (default 5555/TCP).
- 定期的にキューからメッセージを取り出し、メッセージ内容に応じて処理(AWS APIやvSphere APIにアクセス)
- Zabbix senderを利用してZabbixにデータを登録

## GateOne Serverコンポーネント

GateOne Serverコンポーネントの役割は以下の通りです。

- 複数のSSHコンソール接続セッションをブラウザ上で管理
- 複数の認証鍵情報を管理

# インストール {#install}

## 必要条件

HyClopsの稼働にはサーバに以下をインストールする必要があります。

- Zabbix (2.0以上) (zabbix senderも含む)
- Python (2.6以上)
- python-setuptools
- ZeroMQ
- ipmitool
- GateOne (Web上でのSSHコンソール接続機能が必要な場合)

以下、具体的な手順を示します。

## Zabbix ServerおよびZabbix Agentのインストール

ZabbixのインストールについてはZabbix公式マニュアルを参照して下さい。
[Zabbix official manual](https://www.zabbix.com/documentation/2.0/manual/installation)

Zabbix AgentはHyClopsおよびGateOneのプロセス稼働監視のために利用します。

##事前準備

Zabbix管理画面の"管理 > 一般 > 値のマッピング"から以下の2つの設定を行います。

**Script return code**

|受信データ|マッピング文字列|
|---------|----------------|
|0|success|
|1|failure|

**Libcloud Node State**

|受信データ|マッピング文字列|
|---------|----------------|
|0|running|
|1|rebooting|
|2|terminated|
|3|pending|
|4|stopped|


## 関連パッケージのインストール

RHEL/CentOSの場合

    Add ZeroMQ package repository (This is the process for CentOS6.)
    $ sudo curl http://download.opensuse.org/repositories/home:/fengshuo:/zeromq/CentOS_CentOS-6/home:fengshuo:zeromq.repo > /etc/yum.repos.d/zeromq.repo
    Install related package
    $ sudo yum install gcc gcc-c++ zeromq zeromq-devel python-devel python-setuptools ipmitool

Ubuntuの場合

    $ sudo apt-get install gcc g++ libzmq1 ipmitool python-dev python-setuptools

## Pythonモジュールのインストール

    $ sudo pip install apache-libcloud==0.13.2 zabbix-api pyzmq psphere python-daemon==1.6 configobj
    Pythonのバージョンが2.7未満の場合ordereddictおよびargparseもインストール
    $ sudo pip install ordereddict argparse
    AWSの課金情報監視を実施したい場合botoもインストール
    $ sudo pip install boto

## GateOneのインストール (オプション機能)

GateOneの基本的なインストール手順はGateOne公式マニュアルを参照して下さい。
[GateOne official manual](http://liftoff.github.io/GateOne/About/index.html)

GateOneの初期設定(API認証設定含む)

    $ sudo /opt/gateone/gateone.py --auth=api --origins="http://zabbix-server-frontend/"
    $ sudo /opt/gateone/gateone.py --new_api_key
    $ sudo service gateone start

RHEL/CentOSの場合

    $ sudo chkconfig gateone on

Ubuntuの場合

    $ sudo update-rc.d gateone defaults

## HyClopsのインストール

    $ wget https://github.com/tech-sketch/hyclops/archive/[version no.].tar.gz
    $ tar zxvf hyclops-[version no.].tar.gz
    $ cd hyclops-[version no.]
    $ sudo python setup.py install

### 起動スクリプト、外部チェックスクリプトの配置

    $ sudo cp -a ./misc/init.d/redhat/hyclops /etc/init.d/  # in case of SysV init
    $ sudo cp -a ./misc/init.d/ubuntu/hyclops.conf /etc/init/   # in case of Upstart
    $ sudo cp -a ./externalscripts/* [externalscripts dir] (/etc/zabbix/externalscripts/ etc...)

### 権限設定

    $ sudo chown zabbix:zabbix [externalscripts dir](/etc/zabbix/externalscripts/ etc...)/*
    $ sudo chmod u+x [externalscripts dir](/etc/zabbix/externalscripts/ etc...)/*

### HyClopsの設定

    $ sudo vim /opt/hyclops/hyclops.conf
    [hyclops]
    # listen_address = *          # listen on all network interface
    # listen_address = 127.0.0.1  # listen on specific network interface
    listen_address = 127.0.0.1  # HyClopsのリッスンIPアドレス指定(default 127.0.0.1)
    listen_port = 5555  # HyClopsのリッスンポート指定 (default 5555)
    [zabbix]
    zabbix_server = 127.0.0.1  # Zabbix serverのIPアドレス/ホスト名指定
    zabbix_port = 10051  # Zabbix serverのリッスンポート指定
    frontend_url = http://%(zabbix_server)s/zabbix  # Zabbix server フロントエンドURL指定
    zabbix_user = Admin   # Zabbixログインユーザ名 (host.create API実行権限のあるユーザ)
    zabbix_password = zabbix   # Zabbixログインユーザパスワード
    zabbix_sender = /usr/bin/zabbix_sender   # zabbix_senderのパス指定
    
    [ipmi]
    ipmitool = /usr/bin/ipmitool   # ipmitoolコマンドのパス指定
    
    [logging]
    log_level = WARNING   # HyClopsのログレベル指定
    log_file = /tmp/hyclops.log  # HyClopsのログ出力先指定
    
    [environments]
    # http_proxy = http://proxy.example.com:8080/  # http_proxy環境変数設定
    # https_proxy = http://proxy.example.com:8080/  # https_proxy環境変数設定
    # no_proxy = "localhost,127.0.0.1"  # no_proxy環境変数設定

### SELinux設定(SELinuxを有効化している場合)

HyClops関連のログはデフォルトで/opt/hyclops/logs/hyclops_server.logに出力されます。
このログはHyClopsプロセスから発するログ及び、Zabbixグローバルスクリプト実行時にも発するログが書きこまれます。
HyClopsプロセスから発するログはHyClops起動ユーザ(hyclops)が、Zabbixグローバルスクリプト実行時のログはApacheの起動ユーザが書き込みを行います。
そこで両ユーザから書込みができるようSELinuxの設定を実施します。

    $ sudo chcon -R -t public_content_rw_t /opt/hyclops/logs/
    $ sudo chcon -R -t public_content_rw_t /tmp/suds/ # vSphere操作時に一時出力されるファイルも同様
    $ sudo setsebool -P allow_httpd_anon_write 1

### サーバ起動設定

SysV initを利用する環境の場合

    $ sudo chkconfig hyclops on
    $ sudo service hyclops start

Upstartを利用する環境の場合

    $ sudo initctl start hyclops

## Zabbixのダッシュボード画面関連ファイルの置換

    $ sudo python setup.py replace -d (zabbix frontend document root path) --zabbix-version=(2.0 or 2.2)

## Zabbix templates,scripts,globalmacroデータのインポート

以下の3つのファイルのインポートが必要です。

- misc/import_data/templates.xml
- misc/import_data/globalscripts.xml
- misc/import_data/globalmacros.xml

インポート処理を自動で実施するスクリプトを提供しています。

    $ sudo python setup.py import -f <zabbix frontend url> -u <zabbix username> -p <zabbix password>
    (例: python setup.py import -f http://localhost/zabbix -u Admin -p zabbix)

## cronスクリプトの設定

HyClopsは、AWS上やvSphere ESXi上から存在しなくなった仮想マシン用Zabbixホストを自動的に「Not exist hosts」ホストグループに移動します。
この移動された存在しないホスト情報を一定期間経過後に自動削除するためのcronスクリプトを登録します。

    $ sudo crontab -u hyclops -e
    */5 * * * * python /opt/hyclops/cron_scripts/delete_not_exist_hosts.py

デフォルトでは存在しなくなってから30日経過後に自動削除するよう設定されています。
変更したい場合には、delete_not_exist_hosts.pyの実行オプションとして「-d 経過日数」を指定して実行するようにします。
(例えば、10日後に削除したい場合は「-d 10」と設定します。)

# 設定 {#configure}

Zabbix管理画面からHyClopsの利用に必要な設定を実施します。

## グローバルマクロ設定

|マクロ|値|
|:---|:---|
|{$GATEONE_URL}|GateOneサーバURL (例: https://gateone-server)|
|{$GATEONE_KEY}|GateOne APIキー|
|{$GATEONE_SECRET}|GateOne シークレットキー|
|{$HYCLOPS_SERVER}|HyClopsのリッスンIPアドレス/ホスト名(例: 127.0.0.1)|
|{$HYCLOPS_PORT}|HyClopsのリッスンポート (例: 5555)|

(GateOneのAPIキーおよびシークレットキーは/opt/gateone/server.confに記載されています。)

## Zabbixのホスト登録

**AWS環境監視用ホスト**

<table>
<tr>
  <th>設定項目</th>
  <th colspan="2">設定値</th>
</tr>
<tr>
  <td>テンプレート名</td>
  <td colspan="2">AWSAccount</td>
</tr>
<tr>
  <td rowspan="5">マクロ</td>
  <td>(Required) {$KEY}</td>
  <td>AWSアクセスキー</td>
</tr>
<tr>
  <td>(Required) {$SECRET}</td>
  <td>AWSシークレットキー</td>
</tr>
<tr>
  <td>(Optional) {$VM_TEMPLATES}</td>
  <td>全インスタンスに共通で割り当てたいテンプレート名(カンマ区切りで複数指定可)</td>
</tr>
<tr>
  <td>(Optional) {$VM_TEMPLATES_WINDOWS}</td>
  <td>Windowsインスタンスに共通で割り当てたいテンプレート名(カンマ区切りで複数指定可)</td>
</tr>
<tr>
  <td>(Optional) {$VM_TEMPLATES_LINUX}</td>
  <td>Windows以外のインスタンスに共通で割り当てたいテンプレート名(カンマ区切りで複数指定可)</td>
</tr>
</table>

**vSphere ESXi環境監視用ホスト**

<table>
<tr>
  <th>設定項目</th>
  <th colspan="2">設定値</th>
</tr>
<tr>
  <td>テンプレート名</td>
  <td colspan="2">vSphereESXi</td>
</tr>
<tr>
  <td>SNMPインタフェース</td>
  <td colspan="2">vSphere ESXi管理インタフェース情報を登録</td>
</tr>
<tr>
  <td rowspan="5">マクロ</td>
  <td>(Required) {$KEY}</td>
  <td>ESXi管理ユーザ名</td>
</tr>
<tr>
  <td>(Required) {$SECRET}</td>
  <td>ESXi管理ユーザパスワード</td>
</tr>
<tr>
  <td>(Optional) {$VM_TEMPLATES}</td>
  <td>全VMに共通で割り当てたいテンプレート名(カンマ区切りで複数指定可)</td>
</tr>
<tr>
  <td>(Optional) {$VM_TEMPLATES_WINDOWS}</td>
  <td>WindowsVMに共通で割り当てたいテンプレート名(カンマ区切りで複数指定可)</td>
</tr>
<tr>
  <td>(Optional) {$VM_TEMPLATES_LINUX}</td>
  <td>Windows以外のVMに共通で割り当てたいテンプレート名(カンマ区切りで複数指定可)</td>
</tr>
</table>

**物理マシン環境監視用ホスト**

|設定項目|設定値|
|---|---|
|テンプレート名|IPMI|
|IPMIインタフェース|IPMIインタフェース情報を登録|
|IPMI設定|IPMI監視設定と同様の設定を実施|

**HyClopsプロセス稼働サーバ、GateOneプロセス稼働サーバ用ホスト**

必要に応じて、HyClopsプロセスやGateOneプロセスが稼働するサーバ用のホストを登録します。
登録したホストにプロセス監視及びログ監視設定を含んだテンプレート(「HyClops Server」、「GateOne Server」)を割当てます。
全てZabbix Serverと同じサーバ上で稼働している場合はZabbix Server監視用ホストに対して上記のテンプレートを割当てます。

# 利用方法 {#usage}

## 各環境の監視

ZabbixダッシュボードにアクセスするとオリジナルのZabbixに加えて3つのエリアが追加されています。
(vSphere status, Amazon Web Services status,Pysical Machine status).

![dashboard]({{ site.production_url }}/assets/images/HyClops_dashboard.png)

この追加エリアは各環境の情報を提示します。
例えばAWSの場合、稼働中・停止中のそれぞれのインスタンス数を表示し、マウスオーバーすることでインスタンスリストが表示されます。
さらに、インスタンス名をマウスオーバーするとより詳細な情報を確認することが可能となります。

## 操作(起動/停止/再起動)

Zabbixダッシュボードから各環境のインスタンスに対して操作を実施することができます。

1. 操作したい対象インスタンスのチェックボックスをオンにします(複数インスタンスの選択可)
2. 実行処理をプルダウンメニューから選択
3. 実行

## SSHコンソール接続

ZabbixダッシュボードからvSphere VMまたはAmazon EC2インスタンス(稼働中の場合のみ)に対してSSHコンソール接続を行います。

![ssh_connect]({{ site.production_url }}/assets/images/ssh_connect.png)

![gateone]({{ site.production_url }}/assets/images/gateone.png)

# 問い合わせ先 {#contact}

フィードバックや不明点等以下までお問い合わせ下さい。

[TIS株式会社](http://www.tis.co.jp)  
コーポレート本部　戦略技術センター  
HyClops for Zabbix 担当宛  
<hyclops@ml.tis.co.jp>


# ライセンス {#license}

HyClops for ZabbixはGNU General Public License version2のもとにリリースされています。  
GPLの全文は [こちら](http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt) からご覧頂くことが可能です。

