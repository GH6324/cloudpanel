import time

from django.db import models
from django.core.cache import cache

from django.contrib.auth.models import User
from libs._azure import AzureApi
from libs.common_azure import AzureClass


import datetime

# Create your models here.
class Account(models.Model):
    users = models.ForeignKey(User, verbose_name='所属用户', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='az_account')
    display_name = models.CharField('订阅名称', max_length=255, default='', blank=True)
    email = models.EmailField('Email', default='', blank=True)
    subscription_id = models.CharField('订阅ID', max_length=100, default='', blank=True)
    login_password = models.CharField('登录密码', max_length=255, default='', blank=True)
    password = models.CharField('APP_SECRET', max_length=255, default='', blank=True)
    client_id = models.CharField('APP_ID', max_length=100, db_index=True)
    tenant_id = models.CharField('TENANT', max_length=100, db_index=True)
    status_choices = (
        ('Enabled', '正常'),
        ('Warned', '警告'),
        ('Disabled', '已停止'),
    )
    update = models.BooleanField('是否升级', default=0)
    status = models.CharField('状态', choices=status_choices, max_length=25, default='', blank=True)
    note = models.CharField('备注信息', max_length=50, default='', blank=True)

    create_time = models.DateTimeField('创建时间', null=True, auto_now_add=True)
    update_time = models.DateTimeField('更新时间', null=True, auto_now=True)


    class Meta:
        verbose_name = '账号管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.email

    # 获取 token
    def get_token(self):
        _cache_token = f'{self.client_id}-{self.password}-az-rest-token'
        access_token = cache.get(_cache_token)
        if access_token:
            return access_token
        azApi = AzureApi(self.client_id, self.password, self.tenant_id)
        if not azApi.get_token():
            return False
        cache.set(_cache_token, azApi.access_token, 3400)
        return azApi.access_token

    # 获取
    def get_az_api(self):
        azApi = AzureApi(self.client_id, self.password, self.tenant_id)
        # azApi.get_token()
        access_token = self.get_token()
        if not access_token: return '获取token失败', False
        azApi.get_token(access_token)
        return azApi, True

    # 获取 vm 数量
    def get_vm_count(self):
        count = Vm.objects.filter(account_id=self.id).count()
        return count


    # 创建 VM
    def _creae_vm(self, vm_name, vm_size, image, location='eastasia', username='azureuser', password='@RqnEy7VSf4w', disk_size=64, group_name='AZURE_GROUP'):

        # 初始化api
        aApi = AzureClass(tenant_id=self.tenant_id, secret=self.password, client_id=self.client_id)
        aApi.subscription_id = self.subscription_id

        status = aApi.create_vm(self.subscription_id, group_name, vm_name, vm_size, image, username, password, location, disk_size)
        if not status:
            return f'创建失败: {aApi.get_error_msg()}', False
        vm_data = {
            'name': vm_name,
            'vm_id': aApi.result.vm_id,
            'vm_size': vm_size,
            'account_id': self.id,
            'location': location,
            'status': 'Creating',
            'group': group_name,
            'os_disk': disk_size,
            'nic_name': f'{vm_name}_nic',
            'public_ip_name': f'{vm_name}_public_ip',
            'username': username,
            'password': password,
            'image': image,
        }
        vm_info = Vm.objects.create(**vm_data)
        # 延迟 5 秒获取虚拟机状态
        time.sleep(5)
        vm_info.update_vm_info()
        return '创建成功', True

    # 更新订阅
    def update_subscriptions(self):
        azApi = AzureApi(self.client_id, self.password, self.tenant_id)
        # azApi.get_token()
        access_token = self.get_token()
        if not access_token: return '获取token失败', False
        azApi.get_token(access_token)
        if not azApi.get_subscriptions(): return '获取订阅信息失败', False

        if self.subscription_id in '':
            self.subscription_id = azApi.subscriptionId
        self.display_name = azApi.display_name
        self.status = azApi.status
        self.save()
        return '获取成功', True

    @classmethod
    def check_status(cls, client_id, password, tenant_id):
        try:
            azApi = AzureApi(client_id, password, tenant_id)
            # azApi.get_token()
            access_token = azApi.get_token()
            if not access_token: return '账户验证失败(无法获取token)', False
            azApi.get_token(access_token)
            if not azApi.get_subscriptions(): return '获取订阅信息失败', False

            return '获取成功', True
        except:
            return 'api信息验证失败', False


    @classmethod
    def image_list(cls, name=''):
        _list = {
            'OpenLogic:CentOS:7.5:latest': 'CentOS 7.5',
            'OpenLogic:CentOS:7_9:latest': 'CentOS 7.9',
            'Canonical:UbuntuServer:18.04-LTS:latest': 'Ubuntu 18.04',
            'canonical:0001-com-ubuntu-server-jammy-daily:22_04-daily-lts-gen2:latest': 'Ubuntu 22.04',
            #'Canonical:UbuntuServer:20.04-LTS:latest': 'Ubuntu 20.04',
            #'Canonical:UbuntuServer:21.04-LTS:latest': 'Ubuntu 21.04',
            'Debian:debian-10:10:latest': 'Debian 10.10',
            #'Debian:debian-11:2:latest': 'Debian 11.2',
            'MicrosoftWindowsServer:WindowsServer:2012-Datacenter-smalldisk:latest': 'Win 2012 DC ',
            'MicrosoftWindowsServer:WindowsServer:2016-Datacenter-smalldisk:latest': 'Win 2016 DC',
            'MicrosoftWindowsServer:WindowsServer:2019-Datacenter-smalldisk:latest': 'Win 2019 DC',
        }
        if name in '': return _list
        return _list.get(name)

    @classmethod
    def location_list(cls, name=''):
        _list = {'eastasia': '亚洲-东亚-香港', 'southeastasia': '亚洲-东南亚-新加坡', 'koreasouth': '亚洲-韩国南部-釜山', 'koreacentral': '亚洲-韩国中部-首尔', 'japaneast': '亚洲-日本东部-东京/埼玉', 'japanwest': '亚洲-日本西部-大阪', 'eastus': '北美-美国东部-维吉尼亚州', 'eastus2': '北美-美国东部-维吉尼亚州', 'southcentralus': '北美-美国中南部-德克萨斯州', 'westus2': '北美-美国西部-加利福尼亚州', 'westus3': '北美-美国西部-加利福尼亚州', 'westcentralus': '北美-美国中西部', 'centralus': '北美-美国中部-爱荷华州', 'northcentralus': '北美-美国中北部-伊利诺伊州', 'southindia': '亚洲-印度南部-清奈', 'westindia': '亚洲-印度西部-孟买', 'australiaeast': '大洋洲-澳洲东部-新南威尔士', 'northeurope': '欧洲-北欧-爱尔兰', 'swedencentral': '欧洲-北欧-斯德哥尔摩中部', 'uksouth': '欧洲-英国南部-伦敦', 'westeurope': '欧洲-西欧-荷兰', 'westus': '北美-美国西部-加利福尼亚州', 'southafricanorth': '非洲-南非北部-约翰内斯堡', 'centralindia': '亚洲-印度中部-浦那', 'jioindiawest': '亚洲-印度西部-Jio India West', 'canadacentral': '北美-加拿大中部-多伦多', 'francecentral': '欧洲-法国中部', 'germanywestcentral': '欧洲-德国中西部', 'norwayeast': '欧洲-挪威东部', 'switzerlandnorth': '欧洲-瑞士北部', 'uaenorth': '亚洲-阿拉伯联合酋长国北部', 'brazilsouth': '南美-巴西南部-圣保罗州', 'southafricawest': '非洲-南非西部-开普敦', 'australiacentral': '大洋洲-澳洲中部-堪培拉', 'australiacentral2': '大洋洲-澳洲中部-堪培拉', 'australiasoutheast': '大洋洲-澳洲东南部-维多利亚', 'jioindiacentral': '亚洲-印度中部-Jio India Central', 'canadaeast': '北美-加拿大东部-魁北克', 'francesouth': '欧洲-法国南部', 'germanynorth': '欧洲-德国北部', 'norwaywest': '欧洲-挪威西部', 'swedensouth': '欧洲-北欧-斯德哥尔摩南部', 'switzerlandwest': '欧洲-瑞士西部', 'ukwest': '欧洲-英国西部-卡地夫', 'uaecentral': '亚洲-阿拉伯联合酋长国中部', 'brazilsoutheast': '南美-巴西东南部'}
        # _list = {
        #     'eastasia': '亚洲-香港',
        #     'southeastasia': '亚洲-新加坡',
        #     'japanwest': '亚洲-日本西部',
        #     'japaneast': '亚洲-日本东部',
        #     'koreasouth': '亚洲-韩国南部',
        #     'westus': '北美-美国西部'
        # }
        if name in '': return _list
        return _list.get(name, name)

    # 获取虚拟机列表
    def update_vm_list(self):
        aApi = AzureClass(tenant_id=self.tenant_id, secret=self.password, client_id=self.client_id)
        aApi.subscription_id = self.subscription_id
        if not aApi.get_vm_list(self.subscription_id):
            return '获取虚拟机列表失败', False

        now_time = datetime.datetime.now()
        for vm in aApi.vm_list:
            vm.update({
                'update_time': datetime.datetime.now(),
                'account_id': self.id
            })
            vm_id = vm['vm_id']
            vm_info = Vm.objects.filter(vm_id=vm_id).first()
            if not vm_info:
                Vm.objects.create(**vm)
            else:
                Vm.objects.filter(vm_id=vm_id).update(**vm)
            continue
        Vm.objects.filter(update_time__lt=now_time, account_id=self.id).delete()
        return '更新vm成功', True


        azApi = AzureApi(self.client_id, self.password, self.tenant_id)
        access_token = self.get_token()
        if not access_token: return '获取token失败', False
        azApi.get_token(access_token)
        azApi.subscriptionId = self.subscription_id
        if not azApi.get_vm_list(): return '获取虚拟机列表失败', False
        now_time = datetime.datetime.now()
        for vm in azApi.vm_list:
            vm.update({
                'update_time': datetime.datetime.now(),
                'account_id': self.id
            })
            vm_id = vm['vm_id']
            vm_info = Vm.objects.filter(vm_id=vm_id).first()
            if not vm_info:
                Vm.objects.create(**vm)
            else:
                Vm.objects.filter(vm_id=vm_id).update(**vm)
            continue
        Vm.objects.filter(update_time__lt=now_time, account_id=self.id).delete()
        return '更新vm成功', True


# 虚拟机
class Vm(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE, verbose_name='所属账号',
                                related_name='az_vm_account')
    name = models.CharField('实例名称', max_length=200, default='', blank=True)
    ip = models.GenericIPAddressField('公网IP', blank=True, null=True)
    vm_size = models.CharField('实例规格', max_length=100, default='', blank=True)
    vm_id = models.CharField('实例ID', max_length=100, default='', blank=True)
    image = models.CharField('系统名称', max_length=100, default='', blank=True)

    os_disk = models.PositiveSmallIntegerField('系统盘', default=0)

    nic_name = models.CharField('网络接口', max_length=50, default='', blank=True)
    public_ip_name = models.CharField('公共IP', max_length=50, default='', blank=True)

    username = models.CharField('初始账号', max_length=50, default='', blank=True)
    password = models.CharField('初始密码', max_length=200, default='', blank=True)

    status_choices = (
        ('stopping', '关机中'),
        ('stopped', '已关机'),
        ('running', '运行中'),
        ('Deleting', '删除中'),
        ('Creating', '创建中'),
        ('starting', '启动中')
    )
    status = models.CharField('状态', choices=status_choices, max_length=25, default='', blank=True)
    group = models.CharField('资源组名称', max_length=50, default='', blank=True)
    location = models.CharField('地区', max_length=25, default='', blank=True)

    create_time = models.DateTimeField('创建时间', null=True, auto_now_add=True)
    update_time = models.DateTimeField('更新时间', null=True, auto_now=True)

    class Meta:
        verbose_name = '实例管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def _start(self):
        azApi = AzureApi(self.account.client_id, self.account.password, self.account.tenant_id)
        access_token = self.account.get_token()
        if not access_token: return '获取token失败', False
        azApi.get_token(access_token)
        azApi.subscriptionId = self.account.subscription_id

        # azApi = self.account.get_az_api()
        azApi.group_name = self.group
        return azApi, True

    # 更新 vm 状态
    def update_vm_info(self):
        aApi = AzureClass(tenant_id=self.account.tenant_id, secret=self.account.password, client_id=self.account.client_id)
        aApi.subscription_id = self.account.subscription_id

        if not aApi.get_vm_info(self.account.subscription_id, self.group, self.name):
            return '获取vm信息失败', False

        self.nic_name = aApi.vm_info['nic_name']

        self.ip = aApi.vm_info['ip']
        self.public_ip_name = aApi.vm_info['public_ip_name']
        self.status = aApi.vm_info['status']
        self.save()

        return '更新完成', True



    # 操作 电源
    def vm_action(self, action):
        aApi = AzureClass(tenant_id=self.account.tenant_id, secret=self.account.password,
                          client_id=self.account.client_id)

        if action not in ['start', 'stop', 'restart', 'delete']: return False

        action = action.replace('stop', 'powerOff')

        azApi, status = self._start()

        # 删除实例
        if action in 'delete':
            status = aApi.delete_vm(self.account.subscription_id, self.group, self.name)
            if status: self.delete()
            return status

        if not azApi.vm_poer_action(self.name, action): return False

        return True

    # 重置 IP
    def reset_ip(self):
        aApi = AzureClass(tenant_id=self.account.tenant_id, secret=self.account.password,
                          client_id=self.account.client_id)
        aApi.subscription_id = self.account.subscription_id
        aApi.change_ip(self.account.subscription_id, self.group, self.name)
        self.update_vm_info()
        return True

# 镜像列表
class Images(models.Model):
    pass