"""Extract rule facts, numeric data and positions from a local research checkout.
Usage: python3 scripts/build-reference-data.py /path/to/dadish-cashflow
Does not execute any third-party code or copy card prose or artwork.
"""
import json, pathlib, sys, hashlib, re
root=pathlib.Path(__file__).resolve().parent.parent
source=pathlib.Path(sys.argv[1]); data=source/'src/assets/data'
def read(name):return json.loads((data/(name+'.json')).read_text())
def cards(name):return next(iter(read(name).values()))['cards']
job_names={'Teacher (K-12)':'教师','Nurse':'护士','Police Officer':'警察','Mechanic':'机械师','Truck Driver':'卡车司机','Secretary':'秘书','Engineer':'工程师','Lawyer':'律师','Doctor (MD)':'医生','Airline Pilot':'航空驾驶员','Business Manager':'企业经理','Janitor':'清洁工'}
order=list(job_names)
jobs=[]
for i,name in enumerate(order):
 x=next(x for x in read('careers')['careers']['careerData'] if x['title']==name)
 mapping={'salary':'salary','tax':'taxes','homePayment':'mortgagePayment','schoolPayment':'schoolLoanPayment','carPayment':'carLoanPayment','creditPayment':'creditCardPayment','retailPayment':'retailPayment','other':'otherExpenses','savings':'savings','childCost':'childPerExpense','homeDebt':'mortgageLiability','schoolDebt':'schoolLoanLiability','carDebt':'carLoanLiability','creditDebt':'creditCardLiability','retailDebt':'retailDebtLiability'}
 jobs.append({'id':i,'name':job_names[name],'english':name,**{k:x[v] for k,v in mapping.items()}})
keynames={'3/2HOUSE':'三卧室两卫住宅','2/1CONDO':'两卧室一卫公寓','PLEX':'多户出租住宅','APTHOUSE':'出租公寓楼','PARTNER':'有限合伙投资','PHONE':'公用电话业务','LAUNDRY':'自助洗衣店','CARWASH':'洗车业务','ARCADE':'游戏厅','PIZZA':'披萨店','BED':'民宿','MALL':'购物中心股份','10ACRES':'10 英亩土地','20ACRES':'20 英亩土地','misc':'亲属借款','gold':'10 枚金币','coin':'稀有金币','widget':'零件创业公司','software':'软件创业公司','CD':'银行存单','2BIG':'2BIG 电力优先股','GRO4US':'GRO4US 共同基金','MYT4U':'MYT4U 电子公司','OK4U':'OK4U 制药公司','ON2U':'ON2U 娱乐公司'}
def offer(x,index,deck):
 key=x['key'];stock='stock' in x['type'];typ='stock' if stock else 'property' if key in ['3/2HOUSE','2/1CONDO','PLEX','APTHOUSE'] else 'business' if key not in ['gold','coin','10ACRES','20ACRES','misc'] else 'collectible'
 result={'sourceId':f'{deck}.{index}','anyoneBuy':x['type']=='smalldeal_anystock','name':keynames[key],'key':key,'type':typ,'units':int(x.get('units',1))}
 if stock:
  if x['cost']<0:result.update(type='split',factor=2 if x['cost']==-1 else .5)
  else:
   result.update(symbol=key,price=x['cost'],dividend=x.get('cashflow',0))
   bounds=re.findall(r'\$([\d,]+)',x.get('traderange',''))
   if len(bounds)==2:result.update(rangeMin=int(bounds[0].replace(',','')),rangeMax=int(bounds[1].replace(',','')))
 else:result.update(down=x['downpay'],value=x['cost'],debt=x['mortgage'],income=x['cashflow'])
 return result
small=[offer(x,i,'small') for i,x in enumerate(cards('smalldeal'))]
big=[offer(x,i,'big') for i,x in enumerate(cards('bigdeal'))]
market=[]
for i,x in enumerate(cards('market')):
 mode=x['type'].replace('market_','');market.append({'sourceId':f'market.{i}','mode':mode,'global':x.get('queue')=='true','key':x['key'],'amount':x['cost'],'minUnits':12 if '12 units or more' in x.get('copy1','') else 1})
doodad_names=['朋友聚餐','赌场消费','税务审计','粉刷住宅','购买音响','购买手机','购买音乐唱片','请朋友喝咖啡','打两轮高尔夫','观看球赛','购买手表','购买保龄球','外出晚餐','购买彩票','家具促销','购买画作','汽车空调维修','更换汽车轮胎','购买太阳镜','结婚纪念日','家庭度假','购买鱼竿','观看航展','购买衣服','进修学习','高中同学聚会','观看演唱会','购买高尔夫球','牙医账单','购买咖啡机','购买料理机','购买网球拍','购物','违章停车罚款','更换热水器','子女大学学费','子女生日派对','子女牙齿矫正','女儿婚礼','购买儿童玩具','购买大屏电视','购买新游艇']
doodads=[{'sourceId':f'doodad.{i}','name':doodad_names[i],'cost':x['cost'],'child':x.get('child'),'payment':x.get('payment',0)} for i,x in enumerate(cards('doodads'))]
ft_names={0:'儿童投资学校',2:'暖通空调服务',3:'帆船比赛',4:'卡车配件工厂',6:'戛纳电影节',7:'收购金矿',8:'蒙大拿湖畔钓鱼小屋',10:'以你命名的公园',11:'炸鸡连锁店',12:'竞选市长',13:'美容院',14:'支持信仰事业',15:'汽车维修店',16:'阿尔卑斯直升机滑雪',17:'俄罗斯石油项目',18:'与总统共进晚餐',19:'T 恤连锁店',20:'癌症与艾滋病研究中心',22:'游览世界七大奇迹',23:'软件公司上市',24:'保护海洋哺乳动物',26:'私人飞机旅行',27:'60 户公寓楼',28:'环球高尔夫之旅',29:'披萨连锁店',30:'儿童图书馆',31:'200 间迷你仓库',32:'南太平洋海岛假期',33:'生物科技公司上市',34:'创业者和平服务团',35:'干洗店',36:'地中海邮轮旅行',38:'城市迷你农场',39:'厨具电视直销业务',40:'非洲摄影之旅',42:'购买森林',43:'家庭餐厅连锁',44:'职业球队贵宾包厢',45:'汉堡连锁店',46:'亚洲古城之旅',47:'便利店连锁'}
fast=[None]*48
for x in read('fasttrack')['fasttrack']['spaces']:
 fast[x['id']]={'type':'dream' if x['type']=='dream' else 'business','name':ft_names[x['id']],'cost':x['cost'],'income':x.get('cashflow',0),'rollmin':x.get('rollmin',0),'reward':x.get('reward',0),'artKey':x.get('icon')}
for i,typ,name in [(1,'charity','慈善'),(5,'payday','现金流日'),(9,'tax','税务审计'),(21,'payday','现金流日'),(25,'divorce','离婚'),(37,'payday','现金流日'),(41,'lawsuit','诉讼')]:fast[i]={'type':typ,'name':name}
template=read('templates/game_screen')['template'];rr=[None]*24;positions={'rat':[None]*24,'fast':[None]*48}
for key,x in template.items():
 if not (key.startswith('rr_') or key.startswith('ft_')):continue
 prefix,kind,number=key.split('_');index=int(number);stage='rat' if prefix=='rr' else 'fast'
 positions[stage][index]={'x':round((float(x['x'])-52.15)/922*100,3),'y':round((float(x['y'])-86)/610*100,3),'w':round(float(x['width'])/922*100,3),'h':round(float(x['height'])/610*100,3)}
 if stage=='rat':rr[index]={'deal':'opportunity','downsize':'downsized'}.get(kind,kind)
dreams=[{'name':x['name'],'cost':x['cost'],'position':i,'icon':'☆','artKey':x.get('artKey')} for i,x in enumerate(fast) if x['type']=='dream']
result={'revision':'classic-research-v3','jobs':jobs,'track':rr,'small':small,'big':big,'market':market,'doodads':doodads,'fast':fast,'dreams':dreams,'positions':positions}
assert all(rr) and all(fast) and all(positions['rat']) and all(positions['fast'])
(root/'reference-data.js').write_text('/* Numeric rule facts and original Chinese labels. Sources: SOURCES.md. */\n(function(r){const data='+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';if(typeof module!=="undefined"&&module.exports)module.exports=data;else r.ClassicData=data;})(globalThis);\n')
manifest={f:hashlib.sha256((data/(f+'.json')).read_bytes()).hexdigest() for f in ['careers','smalldeal','bigdeal','market','doodads','fasttrack','templates/game_screen','vocab_en_us']}
(root/'reference-manifest.json').write_text(json.dumps({'repository':'https://github.com/dadish/cashflow','commit':'2edcdbc15785ac2141f3d1fe544b14e0de2775b4','sha256':manifest,'copied':'mechanical numeric facts, card category keys, geometric positions; no source code, card prose, audio or artwork'},indent=2)+'\n')
print({k:len(result[k]) for k in ['jobs','small','big','market','doodads','fast','dreams']})
