

menu_top = [
    {
        "label": "首页",
        "path": "/dashboard",
        "icon": 'el-icon-s-home',
        "meta": {
            "i18n": 'dashboard',
        },
        "parentId": 0
    }
]

first = [
    {
        "label": "用户管理",
        "path": '/userinfo',
        "meta": {
            "i18n": 'userinfo',
        },
        "icon": 'el-icon-user-solid',
        "children": [
            {
                "label": "用户管理",
                "path": 'user',
                "component": 'views/userinfo/user',
                "meta": {
                    "i18n": 'user'
                },
                "icon": 'el-icon-user-solid',
                "children": []
            },
            {
                "label": "安全管理",
                "path": 'pw',
                "component": 'views/userinfo/pw',
                "meta": {
                    "i18n": 'user',
                    "keepAlive": True
                },
                "icon": 'el-icon-setting',
                "children": []
            },
            {
                "label": "会员充值规则",
                "path": 'vip',
                "component": 'views/userinfo/vip',
                "meta": {
                    "i18n": 'vip'
                },
                "icon": 'el-icon-user-solid',
                "children": []
            },
        ]
    },
    {
        "label": "店铺管理",
        "path": '/shopinfo',
        "meta": {
            "i18n": 'shopinfo',
        },
        "icon": 'el-icon-menu',
        "children": [
            {
                "label": "轮播图管理",
                "path": '/bannerHandler',
                "component": 'views/shopinfo/bannerHandler',
                "meta": {
                    "i18n": 'bannerHandler'
                },
                "icon": 'el-icon-picture-outline-round',
                "children": []
            }
        ]
    },
    {
        "label": "商品管理",
        "path": '/goodsinfo',
        "meta": {
            "i18n": 'goodsinfo',
        },
        "icon": 'el-icon-s-goods',
        "children": [
            {
                "label": "商品管理",
                "path": '/goods',
                "component": 'views/goodsinfo/goods',
                "meta": {
                    "i18n": 'goods'
                },
                "icon": 'el-icon-s-goods',
                "children": []
            },
            {
                "label": "分类管理",
                "path": '/category',
                "component": 'views/goodsinfo/category',
                "meta": {
                    "i18n": 'category'
                },
                "icon": 'el-icon-menu',
                "children": []
            },
            {
                "label": "规格管理",
                "path": '/sku',
                "component": 'views/goodsinfo/sku/sku',
                "meta": {
                    "i18n": 'sku',
                    "keepAlive": False
                },
                "icon": 'el-icon-menu',
                "children": []
            },
        ]
    },
    # {
    #     "label": "主题管理",
    #     "path": '/themeinfo',
    #     "meta": {
    #         "i18n": 'themeinfo',
    #     },
    #     "icon": 'el-icon-menu',
    #     "children": [
    #         {
    #             "label": "热门分类管理",
    #             "path": '/hotcategory',
    #             "component": 'views/themeinfo/hotcategory',
    #             "meta": {
    #                 "i18n": 'hotcategory',
    #                 "keepAlive": True
    #             },
    #             "icon": 'el-icon-menu',
    #             "children": []
    #         },
    #         {
    #             "label": "热门分类管理1",
    #             "path": '/hotcategory1',
    #             "component": 'views/themeinfo/hotcategory1',
    #             "meta": {
    #                 "i18n": 'hotcategory1',
    #                 "keepAlive": True
    #             },
    #             "icon": 'el-icon-menu',
    #             "children": []
    #         },
    #         {
    #             "label": "推荐分类管理",
    #             "path": '/tjcategory',
    #             "component": 'views/themeinfo/tjcategory',
    #             "meta": {
    #                 "i18n": 'tjcategory',
    #                 "keepAlive": True
    #             },
    #             "icon": 'el-icon-menu',
    #             "children": []
    #         },
    #     ]
    # },
    {
        "label": "订单管理",
        "path": '/orderinfo',
        "meta": {
            "i18n": 'orderinfo',
        },
        "icon": 'el-icon-s-order',
        "children": [
            {
                "label": "订单管理",
                "path": '/order',
                "component": 'views/orderinfo/order',
                "meta": {
                    "i18n": 'order',
                    "keepAlive": False
                },
                "icon": 'el-icon-s-order',
                "children": []
            },
        ]
    },
    {
        "label": "系统管理",
        "path": '/systemManagement',
        "meta": {
            "i18n": 'systemManagement',
        },
        "icon": 'el-icon-setting',
        "children": [
            {
                "label": "app版本管理",
                "path": 'appHandler',
                "component": 'views/systemManagement/appHandler',
                "meta": {
                    "i18n": 'appHandler'
                },
                "icon": 'el-icon-setting',
                "children": []
            },
            {
                "label": "缓存管理",
                "path": 'Cache',
                "component": 'views/systemManagement/Cache',
                "meta": {
                    "i18n": 'Cache'
                },
                "icon": 'el-icon-setting',
                "children": []
            },
        ]
    }
]


all_menu = {
    "top" : menu_top,
    "first" : first
}
