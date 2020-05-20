import tcod as libtcod
from random import randint

import random

from components.ai import BasicMonster, MindControlled
from components.equipment import EquipmentSlots
from components.equippable import Equippable
from components.inventory import Inventory
from components.fighter import Fighter
from components.item import Item
from components.stairs import Stairs
from entity import Entity
from game_messages import Message
from item_functions import cast_confusion, cast_fireball, cast_lightning, heal, cast_sleep, cast_sleep_aura, health_talisman_sacrifice, cast_mind_control, necromancy, recover_mana, cast_magic
from map_objects.rectangle import Rect
from map_objects.tile import Tile

from random_utils import from_dungeon_level, random_choice_from_dict

from render_functions import RenderOrder


class GameMap:
	def __init__(self, width, height, dungeon_level=1):
		self.width = width
		self.height = height
		self.shop_items = []
		self.shop_equipment_items = []
		self.tiles = self.initialize_tiles()

		self.dungeon_level = dungeon_level

	def initialize_tiles(self):
		tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]

		return tiles

	def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, 
		entities, orc_tile, healing_potion_tile, scroll_tile, troll_tile, stairs_tile, sword_tile, 
		shield_tile, dagger_tile, magic_wand_tile, greater_healing_potion_tile, ghost_tile, slime_tile, 
		corpse_tile, goblin_tile, baby_slime_tile, skeleton_tile, slime_corpse_tile, baby_slime_corpse_tile, 
		skeleton_corpse_tile, mana_potion_tile, wizard_staff_tile, health_talisman_tile, basilisk_tile, 
		treasure_tile, chestplate_tile, leg_armor_tile, helmet_tile, amulet_tile):
		rooms = []
		num_rooms = 0

		center_of_last_room_x = None
		center_of_last_room_y = None

		for r in range(max_rooms):
			w = randint(room_min_size, room_max_size)
			h = randint(room_min_size, room_max_size)

			x = randint(0, map_width - w - 1)
			y = randint(0, map_height - h - 1)

			new_room = Rect(x, y, w, h)

			for other_room in rooms:
				if new_room.intersect(other_room):
					break
			else:
				self.create_room(new_room)

				(new_x, new_y) = new_room.center()

				center_of_last_room_x = new_x
				center_of_last_room_y = new_y

				if num_rooms == 0:
					player.x = new_x
					player.y = new_y
				else:
					(prev_x, prev_y) = rooms[num_rooms - 1].center()

					if randint(0, 1) == 1:
						self.create_h_tunnel(prev_x, new_x, prev_y)
						self.create_v_tunnel(prev_y, new_y, new_x)
					else:
						self.create_v_tunnel(prev_y, new_y, prev_x)
						self.create_h_tunnel(prev_x, new_x, new_y)

				self.place_entities(new_room, entities, orc_tile, healing_potion_tile, scroll_tile, 
					troll_tile, stairs_tile, sword_tile, shield_tile, dagger_tile, magic_wand_tile, 
					greater_healing_potion_tile, ghost_tile, slime_tile, corpse_tile, goblin_tile, 
					baby_slime_tile, skeleton_tile, slime_corpse_tile, baby_slime_corpse_tile, 
					skeleton_corpse_tile, mana_potion_tile, wizard_staff_tile, health_talisman_tile, 
					basilisk_tile, treasure_tile, chestplate_tile, leg_armor_tile, helmet_tile, amulet_tile)


				rooms.append(new_room)
				num_rooms += 1

		stairs_component = Stairs(self.dungeon_level + 1)
		down_stairs = Entity(center_of_last_room_x, center_of_last_room_y, stairs_tile, libtcod.white, 'Stairs', render_order=RenderOrder.STAIRS, stairs=stairs_component)
		entities.append(down_stairs)

		treasure_x = center_of_last_room_x + random.choice([-1, 1])
		treasure_y = center_of_last_room_y + random.choice([-1, 1])
		treasure_bucket = randint(1, 20)
		if treasure_bucket == 1:
			gold_value = 20
			item_component = Item(gold=gold_value)
		elif 2 <= treasure_bucket <= 10:
			gold_value = 40
			item_component = Item(gold=gold_value)
		elif 11 <= treasure_bucket <= 15:
			gold_value = 50
			item_component = Item(gold=gold_value)
		elif 16 <= treasure_bucket <= 19:
			gold_value = 60
			item_component = Item(gold=gold_value)
		elif treasure_bucket == 20:
			gold_value = 100
			item_component = Item(gold=gold_value)

		treasure = Entity(treasure_x, treasure_y, treasure_tile, libtcod.white, "Treasure (+" + str(gold_value) + " gold)", render_order=RenderOrder.ITEM, item=item_component)
		entities.append(treasure)


	def create_room(self, room):
		for x in range(room.x1 + 1, room.x2):
			for y in range(room.y1 + 1, room.y2):
				self.tiles[x][y].blocked = False
				self.tiles[x][y].block_sight = False

	def create_h_tunnel(self, x1, x2, y):
		for x in range(min(x1, x2), max(x1, x2) + 1):
			self.tiles[x][y].blocked = False
			self.tiles[x][y].block_sight = False

	def create_v_tunnel(self, y1, y2, x):
		for y in range(min(y1, y2), max(y1, y2) + 1):
			self.tiles[x][y].blocked = False
			self.tiles[x][y].block_sight = False

	def place_entities(self, room, entities, orc_tile, healing_potion_tile, scroll_tile, troll_tile, stairs_tile, 
		sword_tile, shield_tile, dagger_tile, magic_wand_tile, greater_healing_potion_tile, ghost_tile, slime_tile, 
		corpse_tile, goblin_tile, baby_slime_tile, skeleton_tile, slime_corpse_tile, baby_slime_corpse_tile, 
		skeleton_corpse_tile, mana_potion_tile, wizard_staff_tile, health_talisman_tile, basilisk_tile, treasure_tile, 
		chestplate_tile, leg_armor_tile, helmet_tile, amulet_tile):
		max_monsters_per_room = from_dungeon_level([[2, 1], [4, 4], [6, 6], [8, 10]], self.dungeon_level)
		max_items_per_room = from_dungeon_level([[1, 1], [2, 8]], self.dungeon_level)
		number_of_monsters = randint(0, max_monsters_per_room)
		number_of_items = randint(0, max_items_per_room)

		monster_chances = {
			'goblin': from_dungeon_level([[80, 1], [50, 3], [30, 5], [0, 7]], self.dungeon_level),
			'orc': from_dungeon_level([[40, 2], [30, 3], [20, 10]], self.dungeon_level),
			'troll': from_dungeon_level([[10, 3], [40, 5], [60, 7]], self.dungeon_level),
			'basilisk': from_dungeon_level([[20, 7], [30, 9], [40, 11]], self.dungeon_level),
			'ghost': from_dungeon_level([[30, 6]], self.dungeon_level),
			'slime': from_dungeon_level([[30, 8]], self.dungeon_level),
			'skeleton': from_dungeon_level([[30, 3]], self.dungeon_level)
			}

		item_descriptors = [
			'Valor', 'Power', 'Ingenuity', 'Glory', 'Strength', 'Speed', 
			'Wealth', 'Divinity', 'Energy', 'Honor', 'Resistance', 'Greatness',
			'Courage', 'Intelligence'
		]

		item_chances = {
			'healing_potion': from_dungeon_level([[15, 1], [10, 8]], self.dungeon_level),
			'greater_healing_potion': from_dungeon_level([[30, 8]], self.dungeon_level),
			'terrium_sword': from_dungeon_level([[15, 3], [0, 10]], self.dungeon_level),
			'terrium_shield': from_dungeon_level([[15, 3], [0, 10]], self.dungeon_level),
			'terrium_chestplate': from_dungeon_level([[15, 4], [0, 10]], self.dungeon_level),
			'terrium_leg_armor': from_dungeon_level([[15, 4], [0, 10]], self.dungeon_level),
			'terrium_helmet': from_dungeon_level([[20, 3], [0, 10]], self.dungeon_level),
			'terrium_amulet': from_dungeon_level([[10, 4], [0, 10]], self.dungeon_level),
			'ferrium_sword': from_dungeon_level([[15, 10], [0, 20]], self.dungeon_level),
			'ferrium_shield': from_dungeon_level([[15, 10], [0, 20]], self.dungeon_level),
			'ferrium_chestplate': from_dungeon_level([[15, 10], [0, 20]], self.dungeon_level),
			'ferrium_leg_armor': from_dungeon_level([[15, 10], [0, 20]], self.dungeon_level),
			'ferrium_helmet': from_dungeon_level([[20, 10], [0, 20]], self.dungeon_level),
			'ferrium_amulet': from_dungeon_level([[10, 10], [0, 20]], self.dungeon_level),
			'aurium_sword': from_dungeon_level([[15, 20]], self.dungeon_level),
			'aurium_shield': from_dungeon_level([[15, 20]], self.dungeon_level),
			'aurium_chestplate': from_dungeon_level([[15, 20]], self.dungeon_level),
			'aurium_leg_armor': from_dungeon_level([[15, 20]], self.dungeon_level),
			'aurium_helmet': from_dungeon_level([[20, 20]], self.dungeon_level),
			'aurium_amulet': from_dungeon_level([[10, 20]], self.dungeon_level),
			'lightning_spell': from_dungeon_level([[25, 3]], self.dungeon_level),
			'fireball_spell': from_dungeon_level([[25, 4]], self.dungeon_level),
			'confusion_spell': from_dungeon_level([[25, 2]], self.dungeon_level),
			'sleep_spell': from_dungeon_level([[25, 4]], self.dungeon_level),
			'sleep_aura': from_dungeon_level([[25, 5]], self.dungeon_level),
			'health_talisman': from_dungeon_level([[20, 10]], self.dungeon_level),
			'wizard_staff': from_dungeon_level([[25, 10]], self.dungeon_level),
			'mind_control_spell': from_dungeon_level([[25, 15]], self.dungeon_level),
			'necromancy_spell': from_dungeon_level([[20, 10]], self.dungeon_level),
			'mana_potion': from_dungeon_level([[15, 1]], self.dungeon_level)
		}

		for i in range(number_of_monsters):
			x = randint(room.x1 + 1, room.x2 - 1)
			y = randint(room.y1 + 1, room.y2 - 1)

			if not any([entity for entity in entities if entity.x == x and entity.y == y]):
				monster_choice = random_choice_from_dict(monster_chances)

				if monster_choice == 'goblin':
					fighter_component = Fighter(hp=4, defense=0, power=2, magic=0, magic_defense=0, xp=20, mana=0, talismanhp=0, gold=randint(1, 3))
					ai_component = BasicMonster()
					inventory_component = Inventory(26)
					monster = Entity(x, y, goblin_tile, libtcod.white, 'Goblin', blocks=True,
						render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component, inventory=inventory_component)
					#item_component = Item(use_function=cast_magic, damage=2, maximum_range=3)
					#test_item1 = Entity(x, y, magic_wand_tile, libtcod.white, "TEST ITEM 1", item=item_component)
					#monster.inventory.add_item(test_item1)
				elif monster_choice == 'orc':
					fighter_component = Fighter(hp=10, defense=0, power=3, magic=0, magic_defense=1, xp=40, mana=0, talismanhp=0, gold=randint(1, 5))
					ai_component = BasicMonster()
					inventory_component = Inventory(26)
					monster = Entity(x, y, orc_tile, libtcod.white, 'Orc', blocks=True,
						render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component, inventory=inventory_component)
				elif monster_choice == 'troll':
					fighter_component = Fighter(hp=14, defense=2, power=5, magic=0, magic_defense=2, xp=100, mana=0, talismanhp=0, gold=randint(3, 7))
					ai_component = BasicMonster()
					inventory_component = Inventory(26)
					monster = Entity(x, y, troll_tile, libtcod.white, 'Troll', blocks=True, fighter=fighter_component,
						render_order=RenderOrder.ACTOR, ai=ai_component, inventory=inventory_component)
				elif monster_choice == 'ghost':
					fighter_component = Fighter(hp=10, defense=0, power=0, magic=5, magic_defense=2, xp=50, mana=0, talismanhp=0, gold=0)
					ai_component = BasicMonster()
					inventory_component = Inventory(26)
					monster = Entity(x, y, ghost_tile, libtcod.white, 'Ghost', blocks=True,
						render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component, inventory=inventory_component)
				elif monster_choice == 'slime':
					fighter_component = Fighter(hp=10, defense=0, power=3, magic=0, magic_defense=0, xp=50, mana=0, talismanhp=0, gold=randint(2, 4))
					ai_component = BasicMonster()
					inventory_component = Inventory(26)
					monster = Entity(x, y, slime_tile, libtcod.white, 'Slime', blocks=True,
						render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component, inventory=inventory_component)
				elif monster_choice == 'skeleton':
					fighter_component = Fighter(hp=10, defense=0, power=4, magic=0, magic_defense=0, xp=60, mana=0, talismanhp=0, gold=randint(2, 5))
					ai_component = BasicMonster()
					inventory_component = Inventory(26)
					monster = Entity(x, y, skeleton_tile, libtcod.white, 'Skeleton', blocks=True,
						render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component, inventory=inventory_component)
				else:
					fighter_component = Fighter(hp=20, defense=3, power=8, magic=0, magic_defense=3, xp=200, mana=0, talismanhp=0, gold=randint(10, 20))
					ai_component = BasicMonster()
					inventory_component = Inventory(26)
					monster = Entity(x, y, basilisk_tile, libtcod.white, 'Basilisk', blocks=True, fighter=fighter_component,
						render_order=RenderOrder.ACTOR, ai=ai_component, inventory=inventory_component)

				entities.append(monster)

		for i in range(number_of_items):
			x = randint(room.x1 + 1, room.x2 - 1)
			y = randint(room.y1 + 1, room.y2 - 1)

			if not any([entity for entity in entities if entity.x == x and entity.y == y]):
				item_choice = random_choice_from_dict(item_chances)

				if item_choice == 'healing_potion':
					item_component = Item(use_function=heal, amount=20, gold=10)
					item = Entity(x, y, healing_potion_tile, libtcod.white, "Health Potion (+20 HP)", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'greater_healing_potion':
					item_component = Item(use_function=heal, amount=40, gold=20)
					item = Entity(x, y, greater_healing_potion_tile, libtcod.white, "Greater Healing Potion (+40 HP)", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'terrium_sword':
					sword_amount = randint(2, 4)
					equippable_component = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=sword_amount, gold=5)
					item = Entity(x, y, sword_tile, libtcod.white, "Terrium Sword of " + random.choice(item_descriptors) + " (+" + str(sword_amount) + " atk)", equippable=equippable_component)
				elif item_choice == 'terrium_shield':
					shield_amount = randint(1, 2)
					equippable_component = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=shield_amount, gold=3)
					item = Entity(x, y, shield_tile, libtcod.white, "Terrium Shield of " + random.choice(item_descriptors) + " (+" + str(shield_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'terrium_chestplate':
					chestplate_amount = randint(2, 3)
					equippable_component = Equippable(EquipmentSlots.CHEST, defense_bonus=chestplate_amount, gold=10)
					item = Entity(x, y, chestplate_tile, libtcod.white, "Terrium Chestplate of " + random.choice(item_descriptors) + " (+" + str(chestplate_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'terrium_leg_armor':
					leg_amount = randint(1, 3)
					equippable_component = Equippable(EquipmentSlots.LEGS, defense_bonus=leg_amount, gold=3)
					item = Entity(x, y, leg_armor_tile, libtcod.white, "Terrium Leg Armor of " + random.choice(item_descriptors) + " (+" + str(leg_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'terrium_helmet':
					helmet_amount = randint(1, 2)
					equippable_component = Equippable(EquipmentSlots.HEAD, defense_bonus=helmet_amount, gold=2)
					item = Entity(x, y, helmet_tile, libtcod.white, "Terrium Helmet of " + random.choice(item_descriptors) + " (+" + str(helmet_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'terrium_amulet':
					amulet_amount = randint(1, 4)
					equippable_component = Equippable(EquipmentSlots.AMULET, magic_bonus=amulet_amount, gold=3)
					item = Entity(x, y, amulet_tile, libtcod.white, "Terrium Amulet of " + random.choice(item_descriptors) + " (+" + str(amulet_amount) + " mgk)", equippable=equippable_component)
				elif item_choice == 'ferrium_sword':
					sword_amount = randint(6, 10)
					equippable_component = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=sword_amount, gold=17)
					item = Entity(x, y, sword_tile, libtcod.white, "Ferrium Sword of " + random.choice(item_descriptors) + " (+" + str(sword_amount) + " atk)", equippable=equippable_component)
				elif item_choice == 'ferrium_shield':
					shield_amount = randint(4, 6)
					equippable_component = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=shield_amount, gold=15)
					item = Entity(x, y, shield_tile, libtcod.white, "Ferrium Shield of " + random.choice(item_descriptors) + " (+" + str(shield_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'ferrium_chestplate':
					chestplate_amount = randint(5, 7)
					equippable_component = Equippable(EquipmentSlots.CHEST, defense_bonus=chestplate_amount, gold=25)
					item = Entity(x, y, chestplate_tile, libtcod.white, "Ferrium Chestplate of " + random.choice(item_descriptors) + " (+" + str(chestplate_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'ferrium_leg_armor':
					leg_amount = randint(4, 6)
					equippable_component = Equippable(EquipmentSlots.LEGS, defense_bonus=leg_amount, gold=20)
					item = Entity(x, y, leg_armor_tile, libtcod.white, "Ferrium Leg Armor of " + random.choice(item_descriptors) + " (+" + str(leg_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'ferrium_helmet':
					helmet_amount = randint(4, 5)
					equippable_component = Equippable(EquipmentSlots.HEAD, defense_bonus=helmet_amount, gold=7)
					item = Entity(x, y, helmet_tile, libtcod.white, "Ferrium Helmet of " + random.choice(item_descriptors) + " (+" + str(helmet_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'ferrium_amulet':
					amulet_amount = randint(5, 9)
					equippable_component = Equippable(EquipmentSlots.AMULET, magic_bonus=amulet_amount, gold=12)
					item = Entity(x, y, amulet_tile, libtcod.white, "Ferrium Amulet of " + random.choice(item_descriptors) + " (+" + str(amulet_amount) + " mgk)", equippable=equippable_component)
				elif item_choice == 'aurium_sword':
					sword_amount = randint(15, 20)
					equippable_component = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=sword_amount, gold=50)
					item = Entity(x, y, sword_tile, libtcod.white, "Aurium Sword of " + random.choice(item_descriptors) + " (+" + str(sword_amount) + " atk)", equippable=equippable_component)
				elif item_choice == 'aurium_shield':
					shield_amount = randint(8, 13)
					equippable_component = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=shield_amount, gold=40)
					item = Entity(x, y, shield_tile, libtcod.white, "Aurium Shield of " + random.choice(item_descriptors) + " (+" + str(shield_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'aurium_chestplate':
					chestplate_amount = randint(10, 15)
					equippable_component = Equippable(EquipmentSlots.CHEST, defense_bonus=chestplate_amount, gold=60)
					item = Entity(x, y, chestplate_tile, libtcod.white, "Aurium Chestplate of " + random.choice(item_descriptors) + " (+" + str(chestplate_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'aurium_leg_armor':
					leg_amount = randint(8, 13)
					equippable_component = Equippable(EquipmentSlots.LEGS, defense_bonus=leg_amount, gold=50)
					item = Entity(x, y, leg_armor_tile, libtcod.white, "Aurium Leg Armor of " + random.choice(item_descriptors) + " (+" + str(leg_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'aurium_helmet':
					helmet_amount = randint(8, 12)
					equippable_component = Equippable(EquipmentSlots.HEAD, defense_bonus=helmet_amount, gold=45)
					item = Entity(x, y, helmet_tile, libtcod.white, "Aurium Helmet of " + random.choice(item_descriptors) + " (+" + str(helmet_amount) + " def)", equippable=equippable_component)
				elif item_choice == 'aurium_amulet':
					amulet_amount = randint(10, 15)
					equippable_component = Equippable(EquipmentSlots.AMULET, magic_bonus=amulet_amount, gold=35)
					item = Entity(x, y, amulet_tile, libtcod.white, "Aurium Amulet of " + random.choice(item_descriptors) + " (+" + str(amulet_amount) + " mgk)", equippable=equippable_component)
				elif item_choice == 'fireball_spell':
					item_component = Item(use_function=cast_fireball, targeting=True, targeting_message=Message("Left click a target tile for the fireball, or right click to cancel.", libtcod.light_cyan), damage=15, radius=3, mana_cost=20, gold=35)
					item = Entity(x, y, scroll_tile, libtcod.white, "Fireball Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'confusion_spell':
					item_component = Item(use_function=cast_confusion, targeting=True, targeting_message=Message("Left click an enemy to confuse it, or right click to cancel.", libtcod.light_cyan), mana_cost=10, gold=15)
					item = Entity(x, y, scroll_tile, libtcod.white, "Confusion Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'sleep_spell':
					item_component = Item(use_function=cast_sleep, targeting=True, targeting_message=Message("Left click an enemy to make it fall asleep, or right click to cancel.", libtcod.light_cyan), mana_cost=10, gold=15)
					item = Entity(x, y, scroll_tile, libtcod.white, "Sleep Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'sleep_aura':
					item_component = Item(use_function=cast_sleep_aura, targeting=True, targeting_message=Message("Left click a target tile to cast the sleep aura, or right click to cancel.", libtcod.light_cyan), radius=3, mana_cost=20, gold=40)
					item = Entity(x, y, scroll_tile, libtcod.white, "Sleep Aura Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'mind_control_spell':
					item_component = Item(use_function=cast_mind_control, targeting=True, targeting_message=Message("Left click a target tile to cast mind control, or right click to cancel.", libtcod.light_cyan), radius=3, mana_cost=15, gold=50)
					item = Entity(x, y, scroll_tile, libtcod.white, "Mind Control Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'health_talisman':
					item_component = Item(use_function=health_talisman_sacrifice, amount=5, gold=100)
					item = Entity(x, y, health_talisman_tile, libtcod.darker_orange, "Health Talisman", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'wizard_staff':
					item_component = Item(use_function=cast_magic, damage=5, maximum_range=5, gold=100)
					item = Entity(x, y, wizard_staff_tile, libtcod.white, "Wizard Staff", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'necromancy_spell':
					item_component = Item(use_function=necromancy, number_of_monsters=5, mana_cost=20, gold=100)
					item = Entity(x, y, scroll_tile, libtcod.white, "Necromancy Spell", render_order=RenderOrder.ITEM, item=item_component)
				elif item_choice == 'mana_potion':
					item_component = Item(use_function=recover_mana, amount=20, gold=5)
					item = Entity(x, y, mana_potion_tile, libtcod.white, "Mana Potion (+20 MANA)", render_order=RenderOrder.ITEM, item=item_component)
				else:
					item_component = Item(use_function=cast_lightning, damage=30, maximum_range=5, mana_cost=15, gold=25)
					item = Entity(x, y, scroll_tile, libtcod.white, "Lightning Spell", render_order=RenderOrder.ITEM, item=item_component)
				entities.append(item)


	def is_blocked(self, x, y):
		if self.tiles[x][y].blocked:
			return True

		return False

	def next_floor(self, player, message_log, constants):
		self.dungeon_level += 1
		entities = [player]

		self.tiles = self.initialize_tiles()
		self.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'], constants['map_width'], 
		constants['map_height'], player, entities, constants['orc_tile'], constants['healing_potion_tile'], constants['scroll_tile'], 
		constants['troll_tile'], constants['stairs_tile'], constants['sword_tile'], constants['shield_tile'], constants['dagger_tile'], 
		constants['magic_wand_tile'], constants['greater_healing_potion_tile'], constants['ghost_tile'], constants['slime_tile'], 
		constants['corpse_tile'], constants['goblin_tile'], constants['baby_slime_tile'], constants['skeleton_tile'], 
		constants['slime_corpse_tile'], constants['baby_slime_corpse_tile'], constants['skeleton_corpse_tile'], constants['mana_potion_tile'],
		constants['wizard_staff_tile'], constants['health_talisman_tile'], constants['basilisk_tile'], constants['treasure_tile'], 
		constants['chestplate_tile'], constants['leg_armor_tile'], constants['helmet_tile'], constants['amulet_tile'])

		player.fighter.heal(player.fighter.max_hp // 3)

		message_log.add_message(Message("You take a moment to rest, and recover your strength.", libtcod.light_violet))

		return entities