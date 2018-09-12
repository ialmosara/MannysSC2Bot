import sc2, asyncio, random
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import *


class MannysBot(sc2.BotAI):
	def __init__(self):
		self.ITERATIONS_PER_MINUTE = 165

	async def on_step(self, iteration):
		self.iteration = iteration		
		self.MAX_WORKERS = 34

		await self.distribute_workers()
		await self.produce_workers()
		await self.produce_overlords()
		await self.produce_extractor()
		await self.expand()
		await self.produce_queens()
		await self.produce_roaches()
		await self.produce_mutalisks()
		await self.attack()
		await self.queen_injects()
		
	async def produce_workers(self):
		larvae = self.units(LARVA)
		if len(self.units(HATCHERY))*16 > len(self.units(DRONE)):
			if self.can_afford(DRONE) and larvae.exists and self.workers.amount < self.MAX_WORKERS and self.supply_left > 0:
				await self.do(larvae.random.train(DRONE))

	async def produce_overlords(self):
		larvae = self.units(LARVA)
		if (self.supply_left < 2 and not self.already_pending(OVERLORD)):
			if (self.can_afford(OVERLORD) and larvae.exists):
				await self.do(larvae.random.train(OVERLORD))

	async def produce_extractor(self):
		larvae = self.units(LARVA)
		drone = self.units(DRONE).random
		for hatchery in self.units(HATCHERY):
			vespene_geysers = self.state.vespene_geyser.closer_than(15.0, hatchery)
			for geyser in vespene_geysers:
				if not self.can_afford(EXTRACTOR):
					break
				worker = self.select_build_worker(geyser.position)
				if worker is None:
					break
				if self.can_afford(EXTRACTOR) and not self.already_pending(EXTRACTOR):
					if not self.units(EXTRACTOR).closer_than(1.0, geyser):
						await self.do(drone.build(EXTRACTOR, geyser))

	async def expand(self):
		hatcheries = self.units(HATCHERY)
		drone = self.units(DRONE).random
		fully_saturated = True
		for hatchery in hatcheries:
			#BAD LOGIC
			if hatchery.surplus_harvesters < 0:
				fully_saturated = False
		if fully_saturated == True and self.can_afford(HATCHERY) and self.units(HATCHERY).amount < 2 and not self.already_pending(HATCHERY) and not self.known_enemy_units.amount > 0:
			await self.expand_now()

	async def produce_queens(self):
		drone = self.units(DRONE).random
		#if spawning pool doesnt already exist and isnt in progress build one
		if not self.units(SPAWNINGPOOL).exists and not self.already_pending(SPAWNINGPOOL) and self.can_afford(SPAWNINGPOOL):
			await self.build(SPAWNINGPOOL, near=self.units(HATCHERY).first)
		if self.units(SPAWNINGPOOL).exists:
			for hatchery in self.units(HATCHERY):
				if self.units(SPAWNINGPOOL).exists and self.units(QUEEN).amount < 2 and self.can_afford(QUEEN) and not self.already_pending(QUEEN) and not self.already_pending(SPAWNINGPOOL):
					await self.do(hatchery.train(QUEEN))

	async def produce_roaches(self):
		larvae = self.units(LARVA)
		drone = self.workers.random

		if not self.units(ROACHWARREN).exists and self.can_afford(ROACHWARREN) and not self.already_pending(ROACHWARREN) and self.units(SPAWNINGPOOL).exists:
			await self.build(ROACHWARREN, near=self.units(HATCHERY).first)
		if larvae.exists and self.can_afford(ROACH) and self.units(ROACHWARREN).exists and not self.already_pending(ROACHWARREN) and self.supply_left > 1:
			await self.do(larvae.random.train(ROACH))

	async def produce_mutalisks(self):
		larvae = self.units(LARVA)
		drone = self.workers.random
		hq = self.townhalls.first

		#produce spire
		if not self.units(LAIR).exists:
			if self.units(SPAWNINGPOOL).exists and not self.already_pending(SPAWNINGPOOL) and self.can_afford(LAIR) and not self.already_pending(LAIR):
				await self.do(hq.build(LAIR))
		else:
			if not self.units(SPIRE).exists and not self.already_pending(SPIRE) and self.can_afford(SPIRE):
				await self.build(SPIRE, near=self.units(HATCHERY).first)
		if self.units(SPIRE).exists and self.can_afford(MUTALISK) and self.supply_left > 1:
			await self.do(larvae.random.train(MUTALISK))

	async def queen_injects(self):
		if (self.units(QUEEN).exists):
			for queen in self.units(QUEEN).idle:
				abilities = await self.get_available_abilities(queen)
				if (self.units(HATCHERY).ready.first.exists):
					hq = self.units(HATCHERY).ready.first
				else:
					hq = self.units(LAIR).ready.first
				if AbilityId.EFFECT_INJECTLARVA in abilities:
					await self.do(queen(EFFECT_INJECTLARVA, hq))

	async def find_target(self, state):
		if len(self.known_enemy_units) > 0:
			return random.choice(self.known_enemy_units)
		elif len(self.known_enemy_structures) > 0:
			return random.choice(self.known_enemy_structures)
		else:
			return self.enemy_start_locations[0]

	async def attack(self):
		enemy = self.known_enemy_units
		units = {ROACH: [15, 5], 
				MUTALISK: [15, 3]}

		for UNIT in units:
			if self.units(UNIT).amount > units[UNIT][0]:
				for unit in self.units(UNIT).idle:
					await self.do(unit.attack(await self.find_target(self.state)))
			elif self.units(UNIT).amount > units[UNIT][1]:
				for unit in self.units(UNIT).idle:
					if self.known_enemy_units.amount > 0:
						await self.do(unit.attack(random.choice(self.known_enemy_units)))

run_game(maps.get("AbyssalReefLE"), [
	Bot(Race.Zerg, MannysBot()),
	Computer(Race.Terran, Difficulty.Medium)
	], realtime = False)