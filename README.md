命令行输入： pip install pysui
打开mint.py来修改配置
拉到代码的213行，213行以上的代码都不需要改动
需要改的参数包括： daily_mint_times （每日所有账户mint总次数） 例如这个参数设置为100，一共有5个账户来打move，则每个账户每日分配到20次，即约一小时一次 keys （写入账户的key和address，每个账户都是{'key':'...','address':'...'}的形式，每一个{}代表一个账户）
暂时不需要修改的参数：rpc_url，ws_url，mint_fee（打move不需要改）
m.init_address() 这行代码用于从第一个地址向其他地址平均分配sui，如果已经配置好，则删掉这行即可 （注意：配置好指的是每个地址都有一个用于mint的sui 对象，如50sui；和一个用于支付gasfee的sui对象，例如2sui，这两个对象不要合并）
