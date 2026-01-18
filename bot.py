import discord
from discord.ext import commands

TOKEN = "SEU_TOKEN_AQUI"

CATEGORY_NAME = "Partidas"
ADM_ROLE_NAME = "Admin"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

fila = []
partidas_ativas = {}

# ================== EVENT ==================
@bot.event
async def on_ready():
    print(f"✅ Bot online como {bot.user}")

# ================== VIEW BOTÕES ==================
class FilaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Entrar na Fila", style=discord.ButtonStyle.green)
    async def entrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        if user in fila:
            await interaction.response.send_message(
                "❌ Você já está na fila.", ephemeral=True
            )
            return

        fila.append(user)
        await interaction.response.send_message(
            "✅ Você entrou na fila.", ephemeral=True
        )

        if len(fila) >= 2:
            await criar_partida(interaction.guild)

    @discord.ui.button(label="Sair da Fila", style=discord.ButtonStyle.red)
    async def sair(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user

        if user in fila:
            fila.remove(user)
            await interaction.response.send_message(
                "🚪 Você saiu da fila.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Você não está na fila.", ephemeral=True
            )

# ================== FUNÇÃO PARTIDA ==================
async def criar_partida(guild):
    jogador1 = fila.pop(0)
    jogador2 = fila.pop(0)

    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    adm_role = discord.utils.get(guild.roles, name=ADM_ROLE_NAME)

    if category is None or adm_role is None:
        return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        jogador1: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        jogador2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        adm_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    channel = await guild.create_text_channel(
        name=f"partida-{jogador1.name}-vs-{jogador2.name}",
        overwrites=overwrites,
        category=category
    )

    partidas_ativas[channel.id] = [jogador1.id, jogador2.id]

    await channel.send(
        f"🎮 **PARTIDA CRIADA**\n\n"
        f"👤 {jogador1.mention} vs {jogador2.mention}\n"
        f"👮 ADM: {adm_role.mention}\n\n"
        f"Quando terminar, use `!finalizar`"
    )

# ================== COMANDOS ==================
@bot.command()
@commands.has_role(ADM_ROLE_NAME)
async def painel(ctx):
    embed = discord.Embed(
        title="🎯 Fila de Partidas",
        description="Use os botões abaixo para entrar ou sair da fila.",
        color=0x00ff00
    )
    await ctx.send(embed=embed, view=FilaView())

@bot.command()
async def fila(ctx):
    if not fila:
        await ctx.send("📭 Fila vazia.")
    else:
        nomes = "\n".join([user.mention for user in fila])
        await ctx.send(f"📜 **Fila Atual:**\n{nomes}")

@bot.command()
async def finalizar(ctx):
    if ctx.channel.id not in partidas_ativas:
        await ctx.send("❌ Este canal não é uma partida.")
        return

    await ctx.send("✅ Partida finalizada. Canal será apagado em 5 segundos.")
    await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=5))
    del partidas_ativas[ctx.channel.id]
    await ctx.channel.delete()

# ================== ERROS ==================
@painel.error
async def painel_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send("❌ Apenas ADMIN pode criar o painel.")

bot.run(TOKEN)
