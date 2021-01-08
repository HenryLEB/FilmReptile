class Review:
    # 初始化 评论用户的 昵称 评级 时间 具体评论链接 短评论 有用数量（👍） 无用数量（👎） 回应数量
    # 力荐 -> 5星
    # 推荐 -> 4星
    # 还行 -> 3星
    # 较差 -> 2星
    # 很差 -> 1星
    #   没评级 -> 空
    def __init__(self, name, rating, time, url_details, short_content, useful_num, useless_num, reply_num):
        self.name = name
        self.rating = rating
        self.time = time
        self.url_details = url_details
        self.short_content = short_content
        self.useful_num = useful_num
        self.useless_num = useless_num
        self.reply_num = reply_num


