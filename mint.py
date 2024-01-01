from pysui import SuiConfig, SyncClient,ObjectID
from pysui.sui.sui_config import SuiConfig, SignatureScheme
from pysui.sui.sui_builders.get_builders import *
from pysui.sui.sui_txn import SyncTransaction

from pysui.sui.sui_txresults.package_meta import (
    SuiMoveScalarArgument,
    SuiMoveVector,
    SuiParameterReference,
    SuiParameterStruct
)

from pysui.sui.sui_types.scalars import (
    SuiString,
    SuiU8,
    SuiU16,
    SuiU32,
    SuiU64,
    SuiU128,
    SuiU256,
)

from typing import Any
import json
import time

_INT_SCALAR_LOOKUP: dict[str, Any] = {
    "U8": SuiU8,
    "U16": SuiU16,
    "U32": SuiU32,
    "U64": SuiU64,
    "U128": SuiU128,
    "U1256": SuiU256,
}



class Mint:
    def __init__(self,mint_fee) -> None:
        self.keys = []
        self.addresses = []
        for k in keys:
            self.keys.append(k['key'])
            self.addresses.append(k['address'])
        
        self.mint_fee = mint_fee
            
    def init_address(self):
        self.set_action_address(0)
        balance = self.get_balance()
        sui_ob = []
        for b in balance:
            if b['coinType'] == '0x2::sui::SUI':
                sui_ob.append(b)
        if len(sui_ob)>2:
            primary_coin = sui_ob[1]['coinObjectId']
            coin_to_merge = []
            for i in range(2,len(sui_ob)):
                coin_to_merge.append(sui_ob[i]['coinObjectId'])
            self.merge_coin(primary_coin,coin_to_merge)
            
        balance = self.get_balance()
        self.transfer_coin(balance)
        print("地址初始化完成")
        
    def set_action_address(self,number):
        self.cfg = SuiConfig.user_config(rpc_url=rpc_url,prv_keys = [{
                    'wallet_key':self.keys[number],                 
                    'key_scheme': SignatureScheme.ED25519   
                }],ws_url=ws_url)
        self.client = SyncClient(self.cfg)

    def get_balance(self):
        result = self.client.execute(GetAllCoins(owner=self.cfg.active_address))
        if result.is_ok():
            re = json.loads(result.result_data.to_json(indent=2))
            return re['data']
          
    def merge_coin(self,primary_coin,coin_to_merge):
        for_owner= self.client.config.active_address
        
        txn = SyncTransaction(client=self.client, initial_sender=for_owner)
        txn.merge_coins(merge_to=primary_coin, merge_from=coin_to_merge)
        txn.execute()
        
    def transfer_coin(self,balance):
        sui_ob = []
        for b in balance:
            if b['coinType'] == '0x2::sui::SUI':
                sui_ob.append(b)
        addresses_amount = len(self.addresses)
        if len(sui_ob) == 1:
            one_address_amount = int(int(sui_ob[0]['balance'])/addresses_amount)
            for a in self.addresses[1:]:
                self.do_transfer(a,sui_ob[0]['coinObjectId'],one_address_amount)
        if len(sui_ob) == 2:
            larger_object = None
            if int(sui_ob[0]['balance'])>int(sui_ob[1]['balance']):
                larger_object = sui_ob[0]
            else:
                larger_object = sui_ob[1]
                
            one_address_amount = int(int(larger_object['balance'])/addresses_amount)
            for a in self.addresses[1:]:
                self.do_transfer(a,larger_object['coinObjectId'],one_address_amount)
        
        print("sui分配完成")
    
    def do_transfer(self,recipient,from_coin,amount):
        for_owner = self.client.config.active_address
        txn = SyncTransaction(client=self.client, initial_sender=for_owner)
        txn.transfer_sui(
            recipient=ObjectID(recipient),
            from_coin=from_coin,
            amount=int(amount),
        )
        txn.execute()
        time.sleep(5)
        
    def select_sui_ob(self,balance):
        sui_ob = []
        for b in balance:
            if b['coinType'] == '0x2::sui::SUI':
                sui_ob.append(b)
        return sui_ob
    
    def select_max_object(self,sui_ob):
        max_boj = {
            'id':'',
            'balance':0
        }
        for obj in sui_ob:
            if int(obj['balance']) >max_boj['balance']:
                max_boj = {
                    'id':obj['coinObjectId'],
                    'balance':int(obj['balance'])
                }
        
        return max_boj
                
    def mint(self,mint_interval):
        for i in range(0,len(keys)):
            try:
                print(f"本轮mint到第{i}个地址")
                self.set_action_address(i)
                self.do_mint(keys[i])
                time.sleep(mint_interval)
            except Exception as e:
                print(f'错误:{e}')
            
    def do_mint(self,address):
        print(f'当前mint:{self.client.config.active_address}')
        coins = self.get_balance()
        sui_ob = self.select_sui_ob(coins)
        if len(sui_ob)>=2:
            max_obj = self.select_max_object(sui_ob)
            if max_obj['balance']>int(self.mint_fee*10**9):
                self.move_call(max_obj)
            else:
                print("地址中sui数量不足0.1")
                
        else:
            print("没有足够的sui object,请向该地址再打一次sui用作gas")
        
    def _recon_args(self,args: list[str], parms: list) -> list[Any]:
        """."""
        assert len(args) == len(parms)
        res_args: list[Any] = []
        for index, parm in enumerate(parms):
            if isinstance(parm, SuiParameterReference):
                res_args.append(ObjectID(args[index]))
            elif isinstance(parm, SuiMoveScalarArgument):
                if parm.scalar_type[0] == "U":
                    res_args.append(_INT_SCALAR_LOOKUP[parm.scalar_type](int(args[index])))
                else:
                    res_args.append(args[index])
            elif isinstance(parm, SuiParameterStruct):
                res_args.append(ObjectID(args[index]))
            elif isinstance(parm, SuiMoveVector):

                res_args.append(SuiString(args[index]))
        return res_args

    def move_call(self,max_obj) :
        """Invoke a Sui move smart contract function."""
        for_owner = self.client.config.active_address

        target = '0x830fe26674dc638af7c3d84030e2575f44a2bdc1baa1f4757cfe010a4b106b6a::movescription::mint'
        arguments = [
            '0xfa6f8ab30f91a3ca6f969d117677fb4f669e08bbeed815071cf38f4d19284199',
            'MOVE',
            max_obj['id'],
            '0x0000000000000000000000000000000000000000000000000000000000000006'
        ]
        
        txn = SyncTransaction(client=self.client, initial_sender=for_owner)
        (
            _target_id,
            _module_id,
            _function_id,
            parameters,
            _res_count,
        ) = txn._move_call_target_cache(target)
        
        arguments = self._recon_args(arguments, parameters[:-1])
        
        res = txn.move_call(
            target=target, arguments=arguments)
        
        txn.execute()
        
        
## 节点地址，如果节点挂了可以改为其他节点
rpc_url="https://sui-rpc.publicnode.com"
ws_url="wss://sui-rpc.publicnode.com/websocket"
        

##输入参数
mint_fee = 0.1 ##每次mint时的mintfee，打move不需要修改
daily_mint_times = 100 ##所有地址每日Mint次数，自己按需设定，例如这里设置为100，共有5个账户，那么每个账户每日打20次


##填入key和address，第一个地址被认为是root地址，会从第一个地址平均向其他地址里分配sui，地址数量无上限
##由于sui的object设定，每个地址必须有两个sui object，一个传入合约mint，一个作为gasfee，所以简单的说每个地址在传入mintfee后，还需要再传入一次gasfee
keys = [
    {
    'key':'12345',
    'address':'54321'
    },
    {
    'key':'12345',
    'address':'54321'
    },
    {},
    {}
]


mint_interval = 24*60*60/daily_mint_times
print(f'每{mint_interval}秒mint一次')

m = Mint(mint_fee) 
m.init_address() ##用于使用第一个地址向其他地址打sui，如果每个地址都已经配置好了，把这行删掉即可
while True:
    m.mint(mint_interval)
    ##每次都是所有地址mint一遍