from calendar import c
import discord
from discord.ext import commands, tasks
from datetime import datetime
from time import mktime
from bin.functions import get_embed
from bin.checks import is_transformator_channel

instruction = '''
1. Зайти на сайт Хоёлаба <https://www.hoyolab.com/home> и авторизоваться там
2. Нажать Ctrl+Shift+I или ПКМ -> Посмотреть код
3. Выбрать вкладку консоль сверху
4. Выполнить команду document.cookie
5. Скопировать и прислать мне вывод команды, Нья!
'''

class Genshin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.claim_daily_reward.start()
        self.resin_cup_alert.start()
        

    @commands.command(
        name = 'auth',
        description='Авторизация для использования данных с Хоёлаба',
        help='transformator',
        )
    @commands.check(is_transformator_channel)
    async def genshin_auth(self, ctx):
        dm_channel = ctx.author.dm_channel
        author_id = ctx.author.id
        if dm_channel == None:
            dm_channel = await ctx.author.create_dm()
        
        await dm_channel.send('Шаги авторизации:' + instruction)
        await ctx.reply('Отправила тебе в лс инструкцию.')

        def check(m):
            return m.author.id == author_id and m.channel == dm_channel

        msg = await self.bot.wait_for('message', check=check)
        
        for atr in msg.content.split('; '):
            if atr.startswith('ltoken'):
                ltoken = atr.split('ltoken=')[1]

            if atr.startswith('ltuid'):
                ltuid = atr.split('ltuid=')[1]

        await dm_channel.send('Супер, а теперь пришли мне UID своего genshin аккаунта, с которого я буду брать информацию.')
        msg = await self.bot.wait_for('message', check=check)
        uid = msg.content

        import genshinstats as gs
        from genshinstats import errors
        try:
            gs.set_cookie(ltuid=ltuid, ltoken=ltoken)
            gs.get_notes(uid)
        except errors.NotLoggedIn:
            return await dm_channel.send('Ошибка авторизации, проверь пожалуйста свои данные!')

        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]

        if not exists_user:
            response = self.bot.db.insert(
                'genshin_stats', 
                author_id,
                ltuid,
                uid,
                ltoken,
                False,
                False
            )
        else:
            return await dm_channel.send('Ты уже авторизован, бака!')
        if response:
            await dm_channel.send(f'Успешно авторизовала тебя!')
        else:
            await dm_channel.send(f'Не удалось авторизоваться, попробуй позже.')

    @commands.command(
        name = 'resin',
        aliases=['смола'],
        description='Краткая сводка по смоле',
        )
    async def genshin_resin(self, ctx):
        data = await self.get_genshin_data(ctx)
        if not data: return
        resin_timer = int(mktime(datetime.now().timetuple()) + int(data['until_resin_limit']))
        realm_timer = int(mktime(datetime.now().timetuple()) + int(data['until_realm_currency_limit']))
        fields = []
        fields.append({'name': f'Твоя смола - {data["resin"]} <:resin:1000684701331234857>', 'value': f'До 160 - <t:{resin_timer}:R>', 'inline': False})
        fields.append({'name': f'Монеток в чайнике - {data["realm_currency"]} 🫖', 'value': f'До полной чаши - <t:{realm_timer}:R>', 'inline': False})

        embed = get_embed(title = 'Краткая сводка.', fields = fields)
        await ctx.reply(embed = embed)

    @commands.command(
        name = 'notes',
        aliases=['заметки'],
        description='Подробная информация твоего аккаунта',
        help='transformator',
        )
    @commands.check(is_transformator_channel)
    async def genshin_notes(self, ctx):
        data = await self.get_genshin_data(ctx)
        if not data: return
        resin_timer = int(mktime(datetime.now().timetuple()) + int(data['until_resin_limit']))
        realm_timer = int(mktime(datetime.now().timetuple()) + int(data['until_realm_currency_limit']))
        cookie = self.bot.db.custom_command(f'select daily_sub, resin_sub, uid from genshin_stats where id = {ctx.author.id};')[0]
        fields = []
        fields.append({'name': f'Твоя смола - {data["resin"]} <:resin:1000684701331234857>', 'value': f'До 160 - <t:{resin_timer}:R>', 'inline': False})
        fields.append({'name': f'Монеток в чайнике - {data["realm_currency"]} 🫖', 'value': f'До полной чаши - <t:{realm_timer}:R>', 'inline': False})
        fields.append({'name': f'Сколько выполнено дейликов - {data["completed_commissions"]}', 'value': f'Забрана ли награда за дейлики - {"Да" if data["claimed_commission_reward"] else "Нет"}', 'inline': False})
        fields.append({'name': f'Подписка на сбор дейли отметок', 'value': f'{"Да" if cookie[0] else "Нет"}', 'inline': False})
        fields.append({'name': f'Подписка на кап смолы', 'value': f'{"Да" if cookie[1] else "Нет"}', 'inline': False})
        fields.append({'name': f'Сколько скидок для боссов осталось', 'value': f'{data["remaining_boss_discounts"]}', 'inline': False})

        embed = get_embed(title = f'Заметки путешественника [{cookie[2]}]', fields = fields)
        await ctx.reply(embed = embed)

    @commands.command(
        name = 'drs',
        help='transformator',
        description='Подписка на сбор дейли отметок',
        )
    @commands.check(is_transformator_channel)
    async def genshin_daily_reward_claim_sub(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            return await ctx.reply('Ты не авторизован, бака!')
        response = self.bot.db.update('genshin_stats', 'daily_sub', 'id', True, author_id)

        if response:
            await ctx.reply('Записала тебя на автоматический сбор дейли отметок.')
        else:
            await ctx.reply('Не получилось записать тебя, попробуй позже.')

    @commands.command(
        name = 'undrs',
        help='transformator',
        description='Отписка от сбора дейли отметок',
        )
    @commands.check(is_transformator_channel)
    async def genshin_daily_reward_claim_unsub(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            return await ctx.reply('Ты не авторизован, бака!')
        response = self.bot.db.update('genshin_stats', 'daily_sub', 'id', False, author_id)

        if response:
            await ctx.reply('Успешно отписала тебя от автоматического сбора дейли отметок.')
        else:
            await ctx.reply('Не получилось отписать тебя, попробуй позже.')

    @commands.command(
        name = 'crs',
        help='transformator',
        description='Подписка на алёрт капа смолы.',
        )
    @commands.check(is_transformator_channel)
    async def genshin_cup_resin_sub(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            return await ctx.reply('Ты не авторизован, бака!')
        response = self.bot.db.update('genshin_stats', 'resin_sub', 'id', True, author_id)

        if response:
            await ctx.reply('Записала тебя на алёрт капа смолы.')
        else:
            await ctx.reply('Не получилось записать тебя, попробуй позже.')

    @commands.command(
        name = 'uncrs',
        help='transformator',
        description='Отписка от алёрта капа смолы.',
        )
    @commands.check(is_transformator_channel)
    async def genshin_cup_resin_unsub(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            return await ctx.reply('Ты не авторизован, бака!')
        response = self.bot.db.update('genshin_stats', 'resin_sub', 'id', False, author_id)

        if response:
            await ctx.reply('Успешно отписала тебя от алёрта капа смолы.')
        else:
            await ctx.reply('Не получилось отписать тебя, попробуй позже.')

    @commands.command(
        name = 'ss',
        aliases=['подписки'],
        description='Статус подписок.',
        )
    async def genshin_sub_status(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            return await ctx.reply('Ты не авторизован, бака!')
        cookie = self.bot.db.custom_command(f'select daily_sub, resin_sub from genshin_stats where id = {author_id};')[0]
        if cookie:
            fields = []
            fields.append({'name': f'Сбор дейли отметок', 'value': f'{"Да" if cookie[0] else "Нет"}', 'inline': False})
            fields.append({'name': f'Кап смолы', 'value': f'{"Да" if cookie[1] else "Нет"}', 'inline': False})

            embed = get_embed(title = 'Твои подписки', fields = fields)
            await ctx.reply(embed = embed)
        else:
            await ctx.reply('Не получилось прочитать твои подписки, попробуй позже.')

    @tasks.loop(hours=1)
    async def claim_daily_reward(self):
        if datetime.now().hour == 17:
            cookies = self.bot.db.custom_command(f'select ltuid, uid, ltoken from genshin_stats where daily_sub = {True};')
            reward_claimed = False
            for cookie in cookies:
                import genshinstats as gs
                gs.set_cookie(ltuid=cookie[0], ltoken=cookie[2])
                reward = gs.claim_daily_reward(cookie[1])
                if reward:
                    reward_claimed = True
                print(reward)
            if reward_claimed:
                channel = await self.bot.fetch_channel(self.config['channel']['main'])
                await channel.send('Собрала ежедневные отметки, Нья!')


    @claim_daily_reward.before_loop
    async def before_claim_daily_reward(self):
        print('waiting claim_daily_reward')
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=10)
    async def resin_cup_alert(self):

        cookies = self.bot.db.custom_command(f'select ltuid, uid, ltoken, resin_alerted, id from genshin_stats where resin_sub = {True};')
        channel = await self.bot.fetch_channel(self.config['channel']['main'])
        for cookie in cookies:
            import genshinstats as gs
            ltuid = cookie[0]
            uid = cookie[1]
            ltoken = cookie[2]
            user_id = cookie[4]
            import genshinstats as gs
            gs.set_cookie(ltuid=ltuid, ltoken=ltoken)
            data = gs.get_notes(uid)
            if data['resin'] >= 155 and not cookie[3]:
                response = self.bot.db.update('genshin_stats', 'resin_alerted', 'id', True, user_id)
                if response:
                    await channel.send(f'<@{user_id}>, Вижу у тебя уже 155 смолы, время сливать? <:blushDetective:860444156386869288>')
                else:
                    print(f'error {response}, {user_id} resin alert')
            
            if data['resin'] < 155 and cookie[3]:
                response = self.bot.db.update('genshin_stats', 'resin_alerted', 'id', False, user_id)
                if not response:
                    print(f'error {response}, {user_id} resin alert')
        
            


    @resin_cup_alert.before_loop
    async def before_resin_cup_alert(self):
        print('waiting resin_cup_alert')
        await self.bot.wait_until_ready()


    async def get_genshin_data(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            await ctx.reply('Ты не авторизован, бака!')
            return 0
        cookie = self.bot.db.custom_command(f'select ltuid, uid, ltoken from genshin_stats where id = {author_id};')[0]
        ltuid = cookie[0]
        uid = cookie[1]
        ltoken = cookie[2]
        import genshinstats as gs
        gs.set_cookie(ltuid=ltuid, ltoken=ltoken)
        return gs.get_notes(uid)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            channel = self.config['channel']['transformator']
            await ctx.send(f'Низя использовать эту команду туть. Тебе сюда <#{channel}>')


    


def setup(bot):
    bot.add_cog(Genshin(bot))