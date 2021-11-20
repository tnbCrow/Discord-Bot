import discord
import os
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option
from core.utils.shortcuts import get_or_create_tnbc_wallet, get_or_create_discord_user
from django.conf import settings
from asgiref.sync import sync_to_async
from escrow.models.escrow import Escrow
from django.db.models import Q, F
from core.models.wallets import ThenewbostonWallet
from core.utils.shortcuts import convert_to_decimal, convert_to_int
from core.models.statistics import Statistic
from escrow.utils import get_or_create_user_profile


class escrow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_subcommand(base="escrow",
                            name="status",
                            description="Escrow TNBC with another user.",
                            options=[
                                create_option(
                                    name="escrow_id",
                                    description="Enter escrow id you want to check the status of.",
                                    option_type=3,
                                    required=True
                                )
                            ]
                            )
    async def escrow_status(self, ctx, escrow_id: str):

        await ctx.defer(hidden=True)

        discord_user = get_or_create_discord_user(ctx.author.id)

        if Escrow.objects.filter(Q(initiator=discord_user) | Q(successor=discord_user), Q(uuid_hex=escrow_id)).exists():
            escrow_obj = await sync_to_async(Escrow.objects.get)(uuid_hex=escrow_id)

            embed = discord.Embed(color=0xe81111)
            embed.add_field(name='ID', value=f"{escrow_obj.uuid_hex}", inline=False)
            embed.add_field(name='Amount', value=f"{convert_to_int(escrow_obj.amount)} TNBC")
            embed.add_field(name='Fee', value=f"{convert_to_int(escrow_obj.fee)} TNBC")
            embed.add_field(name='Buyer Receives', value=f"{convert_to_int(escrow_obj.amount - escrow_obj.fee)} TNBC")
            embed.add_field(name='Price (USDT)', value=convert_to_decimal(escrow_obj.price))
            if discord_user == escrow_obj.successor:
                initiator = await self.bot.fetch_user(int(escrow_obj.initiator.discord_id))
                embed.add_field(name='Your Role', value='Buyer')
                embed.add_field(name='Seller', value=f"{initiator.mention}")
            else:
                successor = await self.bot.fetch_user(int(escrow_obj.successor.discord_id))
                embed.add_field(name='Your Role', value='Seller')
                embed.add_field(name='Buyer', value=f"{successor.mention}")

            embed.add_field(name='Status', value=f"{escrow_obj.status}")

            if escrow_obj.status == Escrow.ADMIN_SETTLED or escrow_obj.status == Escrow.ADMIN_CANCELLED:
                embed.add_field(name='Settled Towards', value=f"{escrow_obj.settled_towards}")
                embed.add_field(name='Remarks', value=f"{escrow_obj.remarks}", inline=False)

        else:
            embed = discord.Embed(title="Error!", description="404 Not Found.", color=0xe81111)

        await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="escrow", name="all", description="All your active escrows.")
    async def escrow_all(self, ctx):

        await ctx.defer(hidden=True)

        discord_user = get_or_create_discord_user(ctx.author.id)

        if Escrow.objects.filter(Q(initiator=discord_user) | Q(successor=discord_user), Q(status=Escrow.OPEN) | Q(status=Escrow.DISPUTE)).exists():
            escrows = await sync_to_async(Escrow.objects.filter)(Q(initiator=discord_user) | Q(successor=discord_user), Q(status=Escrow.OPEN) | Q(status=Escrow.DISPUTE))

            embed = discord.Embed(color=0xe81111)

            for escrow in escrows:

                embed.add_field(name='ID', value=f"{escrow.uuid_hex}", inline=False)
                embed.add_field(name='Amount', value=f"{convert_to_int(escrow.amount)} TNBC")
                embed.add_field(name='Fee', value=f"{convert_to_int(escrow.fee)} TNBC")
                embed.add_field(name='Buyer Receives', value=f"{convert_to_int(escrow.amount - escrow.fee)} TNBC")
                embed.add_field(name='Price (USDT)', value=convert_to_decimal(escrow.price))
                embed.add_field(name='Status', value=f"{escrow.status}")
                embed.set_footer(text="Use /escrow release to release the TNBC once you've received payment or /escrow cancel to cancel the escrow (never cancel escrow once you've transferred payment).")

                if escrow.initiator == discord_user:
                    embed.add_field(name='Your Role', value="Seller")
                else:
                    embed.add_field(name='Your Role', value="Buyer")

        else:
            embed = discord.Embed(title="Oops..", description="No active escrows found.", color=0xe81111)

        await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="escrow",
                            name="release",
                            description="Release escrow to successor.",
                            options=[
                                create_option(
                                    name="escrow_id",
                                    description="Enter escrow id you want to check the status of.",
                                    option_type=3,
                                    required=True
                                )
                            ]
                            )
    async def escrow_release(self, ctx, escrow_id: str):

        await ctx.defer(hidden=True)

        discord_user = get_or_create_discord_user(ctx.author.id)

        if Escrow.objects.filter(uuid_hex=escrow_id, initiator=discord_user).exists():

            escrow_obj = await sync_to_async(Escrow.objects.get)(uuid_hex=escrow_id)

            if escrow_obj.status == Escrow.OPEN:

                escrow_obj.status = Escrow.COMPLETED
                escrow_obj.save()

                seller_wallet = get_or_create_tnbc_wallet(discord_user)
                seller_wallet.balance -= escrow_obj.amount
                seller_wallet.locked -= escrow_obj.amount
                seller_wallet.save()

                buyer_wallet = get_or_create_tnbc_wallet(escrow_obj.successor)
                buyer_wallet.balance += escrow_obj.amount - escrow_obj.fee
                buyer_wallet.save()

                statistic, created = Statistic.objects.get_or_create(title="main")
                statistic.total_fees_collected += escrow_obj.fee
                statistic.save()

                buyer_profile = get_or_create_user_profile(escrow_obj.successor)
                buyer_profile.total_escrows += 1
                buyer_profile.total_tnbc_escrowed += escrow_obj.amount - escrow_obj.fee
                buyer_profile.save()

                seller_profile = get_or_create_user_profile(discord_user)
                seller_profile.total_escrows += 1
                seller_profile.total_tnbc_escrowed += escrow_obj.amount
                seller_profile.save()

                embed = discord.Embed(title="Escrow Released Successfully", description="", color=0xe81111)
                embed.add_field(name='ID', value=f"{escrow_obj.uuid_hex}", inline=False)
                embed.add_field(name='Amount', value=f"{convert_to_int(escrow_obj.amount)} TNBC")
                embed.add_field(name='Fee', value=f"{convert_to_int(escrow_obj.fee)} TNBC")
                embed.add_field(name='Buyer Received', value=f"{convert_to_int(escrow_obj.amount - escrow_obj.fee)} TNBC")
                embed.add_field(name='Price (USDT)', value=convert_to_decimal(escrow_obj.price))
                embed.add_field(name='Status', value=f"{escrow_obj.status}")

                conversation_channel = self.bot.get_channel(int(escrow_obj.conversation_channel_id))
                await conversation_channel.send(embed=embed)

                recent_trade_channel = self.bot.get_channel(int(settings.RECENT_TRADE_CHANNEL_ID))
                await recent_trade_channel.send(f"Recent Trade: {convert_to_int(escrow_obj.amount)} TNBC at ${convert_to_decimal(escrow_obj.price)} each")

            else:
                embed = discord.Embed(title="Error!", description=f"You cannot release the escrow of status {escrow_obj.status}.", color=0xe81111)
        else:
            embed = discord.Embed(title="Error!", description="You do not have permission to perform the action.", color=0xe81111)

        await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="escrow",
                            name="cancel",
                            description="Cancel escrow.",
                            options=[
                                create_option(
                                    name="escrow_id",
                                    description="Enter escrow id you want to check the status of.",
                                    option_type=3,
                                    required=True
                                )
                            ]
                            )
    async def escrow_cancel(self, ctx, escrow_id: str):

        await ctx.defer(hidden=True)

        discord_user = get_or_create_discord_user(ctx.author.id)

        # Check if the user is initiator or successor
        if Escrow.objects.filter(Q(initiator=discord_user) |
                                 Q(successor=discord_user),
                                 Q(uuid_hex=escrow_id)).exists():

            escrow_obj = await sync_to_async(Escrow.objects.get)(uuid_hex=escrow_id)

            if escrow_obj.status == Escrow.OPEN:

                if int(escrow_obj.successor.discord_id) == ctx.author.id:
                    escrow_obj.status = Escrow.CANCELLED
                    escrow_obj.save()

                    ThenewbostonWallet.objects.filter(user=escrow_obj.initiator).update(locked=F('locked') - escrow_obj.amount)

                    embed = discord.Embed(title="Escrow Cancelled Successfully", description="", color=0xe81111)
                    embed.add_field(name='ID', value=f"{escrow_obj.uuid_hex}", inline=False)
                    embed.add_field(name='Amount', value=f"{convert_to_int(escrow_obj.amount)} TNBC")
                    embed.add_field(name='Fee', value=f"{convert_to_int(escrow_obj.fee)} TNBC")
                    embed.add_field(name='Price (USDT)', value=convert_to_decimal(escrow_obj.price))
                    embed.add_field(name='Status', value=f"{escrow_obj.status}")

                    conversation_channel = self.bot.get_channel(int(escrow_obj.conversation_channel_id))
                    await conversation_channel.send(embed=embed)

                else:
                    embed = discord.Embed(title="Error!", description="Only the buyer can cancel the escrow. Use the command /escrow dispute if they're not responding.", color=0xe81111)
            else:
                embed = discord.Embed(title="Error!", description=f"You cannot cancel the escrow of status {escrow_obj.status}.", color=0xe81111)
        else:
            embed = discord.Embed(title="Error!", description="404 Not Found.", color=0xe81111)

        await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="escrow",
                            name="dispute",
                            description="Start an dispute.",
                            options=[
                                create_option(
                                    name="escrow_id",
                                    description="Enter escrow id you want to check the status of.",
                                    option_type=3,
                                    required=True
                                )
                            ]
                            )
    async def escrow_dispute(self, ctx, escrow_id: str):

        await ctx.defer(hidden=True)

        discord_user = get_or_create_discord_user(ctx.author.id)

        if Escrow.objects.filter(Q(initiator=discord_user) |
                                 Q(successor=discord_user),
                                 Q(uuid_hex=escrow_id)).exists():

            escrow_obj = await sync_to_async(Escrow.objects.get)(uuid_hex=escrow_id)

            if escrow_obj.status == Escrow.OPEN:
                escrow_obj.status = Escrow.DISPUTE
                escrow_obj.save()

                dispute = self.bot.get_channel(int(settings.DISPUTE_CHANNEL_ID))

                initiator = await self.bot.fetch_user(int(escrow_obj.initiator.discord_id))
                successor = await self.bot.fetch_user(int(escrow_obj.successor.discord_id))
                agent_role = discord.utils.get(ctx.guild.roles, id=int(os.environ["AGENT_ROLE_ID"]))

                user_profile = get_or_create_user_profile(discord_user)
                user_profile.total_disputes += 1
                user_profile.save()

                dispute_embed = discord.Embed(title="Dispute Alert!", description="", color=0xe81111)
                dispute_embed.add_field(name='ID', value=f"{escrow_obj.uuid_hex}", inline=False)
                dispute_embed.add_field(name='Amount', value=f"{convert_to_decimal(escrow_obj.amount)}")
                dispute_embed.add_field(name='Price (USDT)', value=convert_to_decimal(escrow_obj.price))
                dispute_embed.add_field(name='Seller', value=f"{initiator}")
                dispute_embed.add_field(name='Buyer', value=f"{successor}")
                dispute = await dispute.send(f"{agent_role.mention}", embed=dispute_embed)

                await dispute.add_reaction("👀")
                await dispute.add_reaction("✅")

                embed = discord.Embed(title="Escrow Disputed Successfully", description="", color=0xe81111)
                embed.add_field(name='ID', value=f"{escrow_obj.uuid_hex}", inline=False)
                embed.add_field(name='Amount', value=f"{convert_to_int(escrow_obj.amount)} TNBC")
                embed.add_field(name='Fee', value=f"{convert_to_int(escrow_obj.amount)} TNBC")
                embed.add_field(name='Buyer Receives', value=f"{convert_to_int(escrow_obj.amount - escrow_obj.fee)} TNBC")
                embed.add_field(name='Price (USDT)', value=convert_to_decimal(escrow_obj.price))
                embed.add_field(name='Seller', value=f"{initiator.mention}")
                embed.add_field(name='Buyer', value=f"{successor.mention}")
                embed.add_field(name='Status', value=f"{escrow_obj.status}")

                conversation_channel = self.bot.get_channel(int(escrow_obj.conversation_channel_id))
                await conversation_channel.send(embed=embed)

            else:
                embed = discord.Embed(title="Error!", description=f"You cannot dispute the escrow of status {escrow_obj.status}.", color=0xe81111)

        else:
            embed = discord.Embed(title="Error!", description="404 Not Found.", color=0xe81111)

        await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_subcommand(base="escrow", name="history", description="All your recent escrows.")
    async def escrow_history(self, ctx):

        await ctx.defer(hidden=True)

        discord_user = get_or_create_discord_user(ctx.author.id)

        if Escrow.objects.filter(Q(initiator=discord_user) | Q(successor=discord_user)).exists():
            escrows = (await sync_to_async(Escrow.objects.filter)(Q(initiator=discord_user) | Q(successor=discord_user)))[:8]

            embed = discord.Embed(color=0xe81111)

            for escrow in escrows:

                embed.add_field(name='ID', value=f"{escrow.uuid_hex}", inline=False)
                embed.add_field(name='Amount', value=f"{convert_to_int(escrow.amount)} TNBC")
                embed.add_field(name='Fee', value=f"{convert_to_int(escrow.fee)} TNBC")
                embed.add_field(name='Price (USDT)', value=convert_to_decimal(escrow.price))
                embed.add_field(name='Status', value=f"{escrow.status}")

        else:
            embed = discord.Embed(title="Oops..", description="You've not complete a single escrow.", color=0xe81111)

        await ctx.send(embed=embed, hidden=True)


def setup(bot):
    bot.add_cog(escrow(bot))
