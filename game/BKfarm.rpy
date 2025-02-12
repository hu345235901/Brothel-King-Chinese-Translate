#### Farm classes ####

init -2 python:
    class Installation(object):

        def __init__(self, name, pic, tags, minion_type, skill, rank=0, minions=None):
            self.name = name
            self.pic = Picture(pic, "brothels/farm/" + pic)
            self.tags = tags
            self.minion_type = minion_type
            self.skill = skill
            self.rank = rank
            if minions:
                self.minions = minions
            else:
                self.minions = []
            self.girls = []

        def has_room(self, type="minion", nb=1):
            if nb <= self.rank - len(self.minions):
                return True
            return False

        def count_free_minions(self):
            return sum(1 for mn in self.minions if mn.free and not mn.hurt)

        def get_free_minions(self, nb=1): # Will only return a list if the required number of minions is available

            min_list = []

            if self.count_free_minions() >= nb:
                min_list = rand_choice([mn for mn in self.minions if mn.free and not mn.hurt], nb)

                for mn in min_list:
                    mn.free = False

            return min_list

#        def get_healthy_minions(self):
#            return [min for min in self.minions if not min.hurt]

        def get_hurt_minions(self):
            return [mn for mn in self.minions if mn.hurt]

        def add_minion(self, mn):
            if mn.type != self.minion_type:
                return False, "You cannot add a " + mn.type + " to the " + self.name + " (wrong minion type)."
            elif self.has_room():
                self.minions.append(mn)
                renpy.play(s_moo, "sound")
#                renpy.say ("", "Adding to " + self.name)
                return True, mn.name + ", a level " + str(mn.level) + " " + mn.type + ", has joined the farm's " + self.name + "."
            elif self.can_upgrade():
                if self.rank > 0:
                    renpy.say("", "The " + self.name + " is currently full.")
                else:
                    renpy.say("", "You must build the " + self.name + " first.")
                if renpy.call_screen("yes_no", "Do you want to upgrade " + self.name + " to rank " + str(self.rank+1) + " for " + str(self.get_price()) + " gold?"):
                    if MC.gold < self.get_price() + mn.get_price("buy"):
                        return False, "You do not have enough money to both upgrade the " + self.name + " and buy the minion."
                    MC.gold -= self.get_price()
                    self.rank += 1
                    self.minions.append(mn)
                    return True, "The farm's " + self.name + " has been extended and " + mn.name + ", a level " + str(mn.level) + " " + self.minion_type + ", has joined."
                else:
                    return False, ""
            else:
                return False, "That's impossible. The farm's " + self.name + " is full and cannot be upgraded at the moment."

        def assign_minions(self): # Returns excess girls to be assigned elsewhere automatically

            for mn in self.minions:
                mn.free = True

            rejected = []

            # 'Group' girls get assigned first
            for girl in [g for g in self.girls if farm.programs[g].act == "group"]:
                min_list = self.get_free_minions(2)
                if min_list:
                    farm.programs[girl].minions = min_list
                else:
                    rejected.append(girl)

            # 'Single' girls are assigned next
            for girl in [g for g in self.girls if farm.programs[g].act != "group"]:
                min_list = self.get_free_minions(1)

                if min_list:
                    farm.programs[girl].minions = min_list
                else:
                    rejected.append(girl)

            # Adds a third minion to groups if possible

            for girl in [g for g in self.girls if farm.programs[g].act == "group"]:
                if girl not in rejected:
                    min_list = self.get_free_minions(1)
                    if min_list:
                        farm.programs[girl].minions += min_list

            for girl in rejected:
                self.girls.remove(girl)

            return rejected

        def get_price(self):
            if self.rank >= 5:
                return 0
            return installation_price[self.rank]

        def get_pic(self):
            return self.pic

        def upgrade(self):
            if MC.gold < self.get_price():
                return False, "You don't have enough gold to expand the " + inst.name + "! Stop wasting my time."
            elif self.rank >= 5:
                return False, "The " + self.name + " cannot be extended any further."
            elif self.rank >= district.rank:
                return False, "Extending the " + self.name + " further would draw too much attention to us. Perhaps once you get a higher brothel license, we can grease a few palms and extend our operation?"
            elif renpy.call_screen("yes_no", "Do you really want to upgrade the " + self.name + " for " + str(self.get_price()) + " gold?"):
                MC.gold -= self.get_price()
                self.rank += 1
                renpy.play(s_gold, "sound")
                unlock_pic(self.pic.path)
                return True, "The " + self.name + " has been extended and can now host " + str(self.rank) + " " + self.minion_type + "."
            else:
                return False, ""

        def can_upgrade(self):
            if self.rank >= district.rank:
                return False
            else:
                return True

        def get_intro(self): # Returns the introduction event if there are girls in the installation, an error instead

            if self.girls:
                if len(self.minions) <= 1:
                    text1 = farm_description[self.minion_type + " intro"] % and_text([g.name for g in self.girls])
                else:
                    text1 = farm_description[self.minion_type + " intro plural"] % (and_text([g.name for g in self.girls]), str(len(self.minions)))

                log.add_report(text1)

                return Event(self.get_pic(), char = narrator, text = text1, changes = "", type = "UI")
            else:
                raise AssertionError, "No girls found in this installation."

        def refresh(self):
            self.girls = []
            for mn in self.minions:
                mn.free = True

    class Minion(object):

        def __init__(self, type, level = 0, name = ""):
            self.type = type
            self.level = level
            if name:
                self.name = name
            else:
                self.name = generate_name(type)
            self.target = "Farm minion"
            self.filter = "misc"
            self.equipped = False
            self.xp = minion_xp_to_level[level]
            self.description = minion_description[type]
            self.pic = self.get_random_pic()
            self.free = True
            self.hurt = False
            self.hp = 4

        def get_key(self):
            return (self.level, self.name)

        def get_pic(self, x, y):
            return self.pic.get(x, y)

        def get_random_pic(self):

            d = str(dice(3))

            pic = Picture(self.type + d + ".webp", "NPC/minions/" + self.type + d + ".webp")

            return pic

        def get_price(self, operation="buy"):
            return round_int(minion_price[self.level] * MC.get_modifier(operation))

        def ready_to_level_up(self):
            if self.level < 5 and self.xp >= minion_xp_to_level[self.level+1]:
                return True
            return False

        def level_up(self, forced=False):
            if self.ready_to_level_up() or forced:
                self.level += 1
                return True
            else:
                return False

        def get_description(self):

            des = ""

            if self.hurt:
                if self.type == "machine":
                    des += "\n" + self.name + " is broken and will be retired in " + str(self.hurt) + " days. "
                else:
                    des += "\n" + self.name + " is injured and will be retired in " + str(self.hurt) + " days. "

            des += self.description

            return des

        def heal(self):
            self.hurt = False
            self.hp = 4

        def use_item(self, it):
            if it.target == "minion":
                for eff in it.effects:
                    if eff.type == "gain":
                        if eff.target == self.type + " xp":
                            self.xp += eff.value


    class FarmProgram(object):
        def __init__(self, girl, fixed_duration=False): # name, type, mode, target, auto=False, duration=None, minion_nb=1, minion_type=["stallion", "beast", "monster", "machine"], pop_v=False):

            self.girl = girl
            self.name = ""
            self.target = "no training" # Reminder: target is the training type, use act to check which sex act is actually assigned
            self.act = None
            self.mode = "hard"
            self.holding = farm.default_holding
            self.resting = "intensive"
            self.tired = False
            self.inst_full = False
            self.refused = False
            self.duration = -1
            self.condition = "none"
#            self.minion_types = minion_types
            self.minions = []
            self.auto_inst = True
            self.installation_name = "fascinated"
            self.installation = None # An object (important)
            self.fixed_duration = fixed_duration
            if fixed_duration:
                self.duration = fixed_duration

            self.avoid_weakness = False
            self.notification = False # Whether or not the player has been shown the girl's reaction to this training program

        def update(self):
            if self.target != "no training":
                self.name = "{color=[c_orange]}" + self.target.capitalize() + " training"  + "{/color}"
            elif self.holding == "rest":
                self.name = "{color=[c_lightgreen]}" + farm_holding_dict[self.holding] + "{/color}"
            else:
                self.name = "{color=[c_cream]}" + farm_holding_dict[self.holding] + "{/color}"

            if self.installation:
                self.installation_name = self.installation.name
            else:
                self.installation_name = "auto"

            self.notification = False

        def refresh(self):
            self.act = None
            self.minions = []
            self.tired = False
            self.inst_full = False
            self.refused = False

            if self.auto_inst:
                self.installation = None

        def resolve(self, type):

            girl = self.girl
            descript = ""
            changes = defaultdict(int)
            pic = None
            pic_bg = None
            text_changes = ""
            events = []
            ev_sound = None

            ## RESOLVE TRAINING ##

#            girl.add_log("farm_days")

            if not isinstance(girl, Girl):
                return events

            if type == "training":

                if not self.act:
                    raise AssertionError, "No act found"
                if not self.installation:
                    raise AssertionError, "No installation found"

                rebel = False
                training_stop = False
                run_away = False
                training_modifier = 0

                # Init description

                min_type = self.minions[0].type

                ## Checks girl reaction to training ##

                reaction = girl.will_do_farm_act(self.act)

                if reaction == "accepted":
                    if self.mode == "soft":
                        MC.evil -= 0.3

                    log.add_report(girl.fullname + " accepted training at the farm.")

                elif reaction == "resisted":
                    training_modifier -= 1
                    MC.good -= 0.3

                    if girl.will_rebel(-25):
                        rebel = True
                    changes["fear"] += 1
                    if not girl.is_("very sub", "lewd"):
                        changes["mood"] -= 2

                elif reaction == "refused":
                    training_modifier -= 2
                    if self.mode == "hardest":
                        MC.evil += 0.3

                    if girl.will_rebel(25):
                        rebel = True
                    changes["fear"] += 2
                    if girl.personality.name not in ("masochist"):
                        changes["mood"] -= 3
                else:
                    raise AssertionError, "Reaction " + reaction + " not recognized."


                # Rebellion attempts

                if rebel:

                    girl.add_log("farm_resisted_training")

                    changes["obedience"] -= 1

                    d = dice(6)

                    if girl.is_("very dom"):
                        mod = +2
                    elif girl.is_("dom"):
                        mod = +1
                    elif girl.is_("very sub"):
                        mod = -1
                    else:
                        mod = 0

                    if d + mod >= 6: # Fight!
#                        descript += event_color["bad"] % (girl.name + " " + reaction + " and tried to fight her! ")

                        fight_res = fight(girl, NPC_gizel, advantage=None)

                        if fight_res == "tie":
                            pic = Picture(path="NPC/gizel/whip1.webp")
                            pic_bg = inst.get_pic()
                            descript += event_color["a little bad"] % (girl.name + " " + reaction + " and attacked Gizel! She was forced to use her magic.\n")
                            ev_sound = s_fire

                            if dice(6) >= 4:
                                girl.get_hurt(dice(5))
                                changes["obedience"] -= dice(3)
                                changes["fear"] += girl.hurt
                                descript += event_color["bad"] % (girl.name + " has been injured and will be out of it for " + str(round_int(girl.hurt)) + " days.")
                                training_stop = True
                                girl.add_log("farm_hurt")

                                calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_resisted", type="morning", call_args=[girl, "rebel girl hurt"]))
                            else:
                                mn = rand_choice(self.minions)
                                mn.hurt = True
                                if mn.type == "machine":
                                    descript += event_color["bad"] % (mn.name + " (level " + str(mn.level) + mn.type + ") was broken in the fighting. It will be retired unless you can repair it.")
                                else:
                                    descript += event_color["bad"] % (mn.name + " (level " + str(mn.level) + mn.type + ") was injured in the fighting. It will be retired unless you can heal it.")
                                changes["obedience"] -= dice(3)
                                changes["fear"] -= dice(3)
                                training_stop = True
                                girl.add_log("minion_hurt")

                                calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_resisted", type="morning", call_args=[girl, "rebel minion hurt"]))

                        elif fight_res: # Girl wins
                            pic = "gizel whip struggling" # Picture(path="NPC/gizel/whip3.webp")
                            pic_bg = inst.get_pic()
                            descript += event_color["bad"] % (girl.name + " " + reaction + "and attacked Gizel, kicking her to the ground before she could use her magic!\n")
                            ev_sound = s_crash

                            if dice(6) >= 4:
                                descript += event_color["bad"] % (girl.name + " ran away into the night.")
                                run_away = True
                                changes["obedience"] -= dice(3) + 2
                                changes["fear"] -= dice(3) + 2
                                training_stop = True
                                girl.add_log("farm_run_away")

                                # calendar.set_alarm(calendar.time+1, Event(label="run_away", object=girl))
                                calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_resisted", type="morning", call_args=[girl, "rebel runaway"]))

                            else:
                                mn = rand_choice(self.minions)
                                mn.hurt = True
                                if mn.type == "machine":
                                    descript += event_color["bad"] % (mn.name + " (level " + str(mn.level) + mn.type + ") was broken in the fighting. It will be retired unless you can repair it.")
                                else:
                                    descript += event_color["bad"] % (mn.name + " (level " + str(mn.level) + mn.type + ") was injured in the fighting. It will be retired unless you can heal it.")
                                changes["obedience"] -= dice(3) + 1
                                changes["fear"] -= dice(3) + 1
                                training_stop = True
                                girl.add_log("minion_hurt")

                                calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_resisted", type="morning", call_args=[girl, "rebel minion hurt"]))

                        else: # Gizel wins
                            pic = "gizel whip happy" # Picture(path="NPC/gizel/whip2.webp")
                            pic_bg = inst.get_pic()
                            descript += event_color["good"] % (girl.name + " " + reaction + " and tried to fight back, but Gizel easily subdued her with a binding spell.\n")
                            ev_sound = s_spell

                            if dice(6) >= 4:
                                descript += event_color["fear"] % ("She lashed out at " + girl.name + "'s sanity, sending her into a fit of terror.")
                                changes["fear"] += dice(3) + 2
                                changes["obedience"] += dice(3)
                                training_stop = True

                            else:
                                descript += event_color["fear"] % ("She used her powers to force " + girl.name + " into a humiliating pose.")
                                changes["fear"] += dice(3)
                                changes["obedience"] += dice(3) + 2
                                training_stop = True

                            calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_resisted", type="morning", call_args=[girl, "rebel subdued"]))
                    else:

                        descript += event_color["a little bad"] % (girl.name + " " + reaction + " training and rebelled against Gizel.\n")

                        if dice(6) >= 3:
                            pic = "gizel whip angry"# Picture(path="NPC/gizel/whip1.webp")
                            pic_bg = inst.get_pic()
                            ev_sound = s_punch
                            descript += event_color["fear"] %  ("Incensed by her insolence, Gizel gave her a vicious whipping.")
                            changes["fear"] += dice(3)
                            changes["obedience"] += dice(3)
                            changes["energy"] -= 10
                            training_stop = True

                        else:
                            pic = farm.pen_pic
                            descript += event_color["a little bad"] % ("Gizel lost interest and left her to rot in her pen instead.")
                            changes["obedience"] -= 1
                            changes["energy"] += 10
                            farm.locked_girls.append(girl)
                            training_stop = True

                        calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_resisted", type="morning", call_args=[girl, "rebel subdued"]))

                    log.add_report(descript)

                elif self.installation: # sanity check
                    if reaction == "accepted":
                        descript += girl.name + " didn't complain and went into the " + self.installation.name + " for her training."
                    elif reaction == "resisted":
                        descript += girl.name + " whined and resisted, but Gizel laughed at her and shoved her into the " + self.installation.name + " anyway."
                        calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_resisted", type="morning", call_args=[girl, "resisted"]))
                    elif reaction == "refused":
                        descript += girl.name + " yelled and cried and pleaded, but Gizel dragged her kicking and screaming into the " + self.installation.name + "."
                        calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_resisted", type="morning", call_args=[girl, "refused"]))

                # Learn from interaction

                if not self.act in farm.knows["reaction"][girl]:
                    farm.knows["reaction"][girl].append(self.act)

                # Stops here and return event if girl fought or resisted successfully

                if training_stop:
                    text_changes = self.apply_changes(girl, changes)
                    events.append(Event(pic = pic, background = pic_bg, char = girl.char, text = descript, changes = text_changes, sound = ev_sound, type = "Health/Security"))

                    if self.duration > 0:
                        self.duration -= 1

                    return events

                # Training continues

                girl.add_log("farm_training_days")

                descript += " "

                if self.act == "group":
                    descript += farm_description[self.act + " intro"] % (girl.fullname, str(len(self.minions)) + " " + rand_choice(minion_adjectives[min_type]) + " " + min_type)
                else:
                    descript += farm_description[self.act + " intro"] % (girl.fullname, article(rand_choice(minion_adjectives[min_type])) + " " + min_type)

                ## Calculates roll modifier

                # Add minion level/group bonus

                training_modifier += sum(mn.level for mn in self.minions) // len(self.minions)

                if len(self.minions) >= 3:
                    training_modifier += 1

                # Test minion weakness

                if self.minions[0].type == girl.weakness or girl.get_effect("special", "all farm weaknesses"):
                    training_modifier += 1
                    weak = True

                    if not farm.knows["weakness"][girl]:
                        descript += " Gizel notices " + girl.name + " reacts strongly in the presence of " + self.minions[0].type + "s (" + event_color["fear"] % "weakness discovered" + ")."
                        farm.knows["weakness"][girl] = farm_installations_dict[girl.weakness]

                        calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_discovered_weakness", call_args=[girl]))

                    else:
                        MC.evil += 0.2
                        if girl.get_effect("special", "all farm weaknesses"):
                            descript += " Gizel knows " + girl.name + " is " + event_color["fear"] % "weak against all farm minions" + ", and uses that against her."
                        else:
                            descript += " Gizel knows " + girl.name + " is especially " + event_color["fear"] % ("weak against " + girl.weakness + "s") + ", and uses that against her."
                else:
                    weak = False

                # Checks act and fix weaknesses

                if self.act in girl.pos_acts and self.act in girl.neg_acts:
                    changes["sensitivity"] += 1

                    if not self.act in farm.knows["amb_acts"][girl]:
                        ev_sound = s_spell
                        descript += " " + girl.name + " was especially tense and confused. " + event_color["average"] % ("Gizel has discovered she is ambivalent about " + long_act_description[self.act] + ".")
                        girl.personality_unlock[self.act] = True
                        farm.knows["amb_acts"][girl].append(self.act)
                    else:
                        descript += " " + girl.name + " struggled, because she has ambivalent feelings about " + long_act_description[self.act] + "."

                elif self.act in girl.pos_acts:
                    changes["libido"] += 1

                    if not self.act in farm.knows["pos_acts"][girl]:
                        ev_sound = s_spell
                        descript += " " + girl.name + " was blushing and breathing heavily, her nipples visibly erect. " + event_color["good"] % ("Gizel has discovered she likes " + long_act_description[self.act] + ".")
                        girl.personality_unlock[self.act] = True
                        farm.knows["pos_acts"][girl].append(self.act)
                    else:
                        descript += " " + girl.name + " is turned on by " + self.act + " acts, so she enjoyed it despite herself."
                    training_modifier += 1

                elif self.act in girl.neg_acts:
                    changes["fear"] += 1
                    if not self.act in farm.knows["neg_acts"][girl]:
                        ev_sound = s_spell
                        descript += " " + girl.name + " was tense and uncooperative, and remained fearful for the whole encounter. " + event_color["a little bad"] % ("Gizel has discovered she dislikes " + long_act_description[self.act] + ".")
                        girl.personality_unlock[self.act] = True
                        farm.knows["neg_acts"][girl].append(self.act)
                    else:
                        descript += " " + girl.name + " doesn't enjoy " + self.act + " acts, so she remained tense and unwilling."

                    training_modifier -= 1

                fix = rand_choice(get_fix_list(self.act))

                if fix.name in [f.name for f in girl.pos_fixations]:
                    training_modifier += 1
                    ev_sound = s_mmmh
                    changes["mood"] += 1
                    changes["libido"] += 1
                    if not fix in farm.knows["pos_fix"][girl]:
                        descript += " During training, Gizel discovered one of " + girl.name + "'s fixations (" + event_color["good"] % fix.name + ")!"
                        girl.personality_unlock[fix.name] = True
                        farm.knows["pos_fix"][girl].append(self.act)
                        test_achievement("pos fixations")
                    else:
                        descript += " Training was more effective, because Gizel used " + girl.name + "'s obsession with " + event_color["good"] % fix.name + " against her."

                elif fix.name in [f.name for f in girl.neg_fixations]:
                    training_modifier += 1
                    ev_sound = s_surprise
                    changes["mood"] -= 1
                    changes["fear"] += 1
                    if not fix in farm.knows["neg_fix"][girl]:
                        descript += " During training, Gizel discovered something " + girl.name + " really hates (" + event_color["fear"] % fix.name + ")."
                        girl.personality_unlock[fix.name] = True
                        farm.knows["neg_fix"][girl].append(self.act)
                        test_achievement("neg fixations")
                    else:
                        descript += " Training was more effective, because Gizel used " + girl.name + "'s disgust for " + event_color["fear"] % fix.name + " against her."


                # Determine result

                roll = dice(6) + training_modifier # Substract girl rank?

                if roll >= 5:
                    final_result = 2.5 #!
                    descript += farm_description[self.minions[0].type + " good"] % girl.name
                elif roll >= 3:
                    final_result = 1.5 #!
                    descript += farm_description[self.minions[0].type + " average"] % girl.name
                else:
                    final_result = 0.5 #!
                    descript += farm_description[self.minions[0].type + " bad"] % girl.name

                base_result = round_up(final_result) # base_result is used with dice() and should always be an integer

                if girl.is_("very sub"):
                    final_result += 1
                elif girl.is_("dom"):
                    final_result -= 0.5
                elif girl.is_("very dom"):
                    final_result -= 1

                if reaction == "accepted":
                    brk, new_pref = girl.raise_preference(self.act, type=None, bonus=final_result*girl.get_effect("boost", "farm sexual training"), status_change=True)
                else:
                    brk, new_pref = girl.raise_preference(self.act, type="fear", bonus=final_result*girl.get_effect("boost", "farm sexual training"), status_change=True)


                # Pop V

                if self.act in ("sex", "group"):
                    if girl.pop_virginity(origin="farm"):
                        changes["obedience"] += 2 + dice(6)
                        descript += "\n{color=[c_lightred]}" + girl.name + " has lost her virginity to " + article(rand_choice(minion_adjectives[self.minions[0].type])) + " " + self.minions[0].type + "!{/color}"
                        log.add_report("{color=[c_lightred]}" + girl.fullname + " has lost her virginity to " + article(rand_choice(minion_adjectives[self.minions[0].type])) + " " + self.minions[0].type + "!{/color}")


                # Stat changes

                changes[self.installation.skill] += dice(base_result+1) - 1
                if self.act in all_sex_acts:
                    changes[self.act] += dice(base_result+1) - 1
                elif self.act == "naked":
                    changes[rand_choice(["obedience", "libido", "beauty", "body"])] += dice(base_result+1) - 1
                elif self.act == "bisexual":
                    changes[rand_choice(["service", "sensitivity", "sex", "libido"])] += dice(base_result+1) - 1
                elif self.act == "group":
                    changes[rand_choice(["service", "sex", "anal", "constitution"])] += dice(base_result+1) - 1

                # BBCR skills degrade over time at the farm

                d = dice(6) # 1: -1 stats, 2-4: -0.5 stat, 5-6: nothing
                if d < 5:
                    changes[rand_choice(["beauty", "body", "charm", "refinement"])] -= 0.5
                    if d == 1:
                        changes[rand_choice(["beauty", "body", "charm", "refinement"])] -= 0.5

                ## Generate event(s)

                text_changes = self.apply_changes(girl, changes)

                # Event if stat maxed out

                if self.act in all_sex_acts:
                    if girl.get_stat(self.act, raw=True) >= girl.get_stat_minmax(self.act, raw = True)[1]:
                        calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_max_skill", type="morning", call_args=[girl, self.act]))

                if girl.get_preference(self.act) == "fascinated":
                    calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_max_pref", type="morning", call_args=[girl, self.act]))

                # Get tired

                t = 5 + dice(10)
                if len(self.minions) > 1:
                    t += 5 + dice(10)

                text1, text2 = girl.tire(t)

                descript += text1
                text_changes += text2

                # Minion level

                for mn in self.minions:
                    mn.xp += girl.rank
                    if mn.level_up():
                        text_changes += event_color["special"] % ("\nMINION LEVEL UP (level " + str(mn.level) + ")")

                # Breaking text

                text_changes += "\n\n" + self.act.capitalize() + ": "

                if brk > 0:
                    text_changes += "{color=[c_green]}"
                    for i in range(int(1 + brk//50)): text_changes += "+"
                    text_changes += "{/color}"
                else:
                    text_changes += "{color=[c_red]}-{/color}"

                # Determines pic (if not already set by a rebel event)

                not_tags = prepare_not_tags(girl, self.act, farm=True) # Reminder: group and bisexual pics are not filtered for the farm

                if self.installation.name == "stables": # May use regular sex pictures for stallions (act > installation.tags)
                    if not pic:
                        pic = girl.get_pic(self.act, and_tags = self.installation.tags, not_tags=not_tags, hide_farm=True, pref_filter=True) # Will exclude beast, monster and machine tags (unless used with fetish act for the latter)

                        if not pic: # Happens if some pictures are disabled
                            attempts = game.last_pic["attempts"]
                            pic = girl.get_pic(self.act, "sex", "naked", attempts=attempts, pref_filter=True)

                else: # May not use regular pictures for monsters, beasts and machines (installation.tags > act)
                    if not pic:
                        pic = girl.get_pic(self.installation.tags, and_tags = self.act, not_tags=not_tags, strict=True, pref_filter=True)

                        if not pic:
                            if self.act != "naked": # Avoids displaying hardcore picture from the girl pack for naked acts
                                attempts = game.last_pic["attempts"]
                                pic = girl.get_pic(self.installation.tags, and_tags = self.act, not_tags=not_tags, attempts=attempts, pref_filter=True)

                            if not pic: # Farm default pictures will always have a 'safe' naked option
                                attempts = game.last_pic["attempts"]
                                pic = farm.get_pic(self.installation.tags, and_tags = self.act, not_tags=not_tags, attempts=attempts)

                # Adjust text (removed as suggested per DougTheC)

                # if count_lines(descript, 85) > 6:
                #     descript = "{size=14}" + descript
                # elif count_lines(descript, 85) > 5:
                #     descript = "{size=16}" + descript
                # else:
                #     descript = "{size=18}" + descript

                # Add main event

                log.add_report(girl.fullname + " has trained " + self.act + " acts in the " + self.installation.name + ".")

                events.append(Event(pic, background = pic_bg, char = girl.char, text = descript, changes = text_changes, sound = ev_sound, type = "Farm"))

                # Adds another event if change of preference status

                if new_pref and new_pref != "refuses":
                    if girl.is_("lewd"):
                        text1 = "lewd"
                    else:
                        text1 = "modest"

                    events.append(Event(pic, char = girl.char, text = (pref_response[text1 + " " + new_pref] % long_act_description[self.act]), changes = text_changes, sound = s_ahaa, type = "special"))

                    text1 = girl.fullname + " is now " + preference_color[new_pref] % new_pref + " with " + self.act + " acts."
                    log.add_report(text1)

                    events.append(Event(pic, char = narrator, text = "\n" + text1, changes = text_changes, sound = s_spell, type = "special"))


            ## RESOLVE RESTING ##

            elif type == "resting" or self.holding == "rest":

                girl.add_log("farm_rest_days")

                if self.tired:
                    if girl.hurt > 0:
                        descript += event_color["bad"] % (girl.fullname + " is hurt and had to rest in her pen today.\n")
                    elif girl.energy <= 0:
                        descript += event_color["bad"] % (girl.fullname + " is exhausted and had to rest in her pen today.\n")
                    descript += event_color["average"] % (girl.fullname + " looked tired, so Gizel left her in her pen today to recuperate (auto-resting: " + self.resting + ").\n")

                elif self.inst_full:
                    descript += event_color["a little bad"] % ("There weren't enough minions available for her training, so " + girl.fullname + " stayed in her pen instead.\n")

                elif self.refused:
                    descript += event_color["bad"] % (girl.fullname + " wouldn't accept training today, so Gizel had no choice but to leave her in her pen") + " (training mode: {i}" + self.mode + "{/i}).\n"

                stat = ""
                text1, text_changes = girl.rest(context="farm")
                descript += text1

                changes["mood"] += 2

                if dice(6) >= 5: # Random chance of event
                    stat = rand_choice(("constitution", "obedience", "sensitivity", "libido"))
                    descript += "\n" + farm_description["pen " + stat] % girl.name
                    changes[stat] += dice(2)

                if stat == "libido":
                    pic = girl.get_pic("mast", "libido", and_tags=["dirty", "hurt"], and_priority=False, not_tags=["group", "bisexual", "sex", "anal"])
                    if not pic:
                        attempts = game.last_pic["attempts"]
                        pic = girl.get_pic("rest", "profile", and_tags = "naked", attempts=attempts)
                else:
                    pic = girl.get_pic("rest", "profile", and_tags=["dirty", "hurt"], and_priority=False, naked_filter=True)

                text_changes += self.apply_changes(girl, changes)

                log.add_report(girl.fullname + " rested in her pen today.")

                events.append(Event(pic, char = girl.char, text = descript, changes = text_changes, type = "Farm"))

            ## RESOLVE HOLDING ##

            else: # Holding

                girl.add_log("farm_holding_days")

                if self.inst_full:
                    descript += event_color["a little bad"] % ("There weren't enough minions available for her training, so " + girl.fullname + " worked in the farm instead")

                elif self.refused:
                    descript += event_color["bad"] % (girl.fullname + " refused to train today, so Gizel had her work around the farm instead ") + "(training mode: {i}" + self.mode + "{/i})"

                else:
                    descript += girl.fullname + " was held at the farm today"

                log.add_report(descript + ", " + farm_holding_dict[self.holding].lower() + ".")

                descript += ".\n" + farm_description["holding " + self.holding] % (girl.name, girl.name)
                act, decreased = farm_holding_stats[self.holding]

                if dice(250) > girl.get_stat(self.holding, raw=True):
                    changes[self.holding] += dice(6) #!

                d = dice(6)

                if d == 1:
                    if dice(250) < girl.get_stat(decreased, raw=True):
                        changes["mood"] -= 2
                        changes[decreased] -= 1
                        descript += farm_description["holding " + self.holding + " bad"] % girl.name
                elif d == 6:
                    changes["mood"] += 1
                    changes[self.holding] += 1
                    brk, new_pref = girl.raise_preference(act, status_change=True)
                    pic = girl.get_pic(act, not_tags=all_sex_acts+["group"])
                    descript += farm_description["holding " + self.holding + " good"] % girl.name
                    text_changes += "\n\n" + act.capitalize() + ": "

                    if brk > 0:
                        text_changes += "{color=[c_green]}"
                        for i in range(int(1 + brk//50)): text_changes += "+"
                        text_changes += "{/color}"
                    elif brk < 0:
                        text_changes += "{color=[c_red]}-{/color}"

                # BBCR skills degrade over time at the farm

                d = dice(6) # 1: -2 stats, 2-4: -1 stat, 5-6: nothing
                if d < 5:
                    changes[rand_choice(["beauty", "body", "charm", "refinement"])] -= 1
                    if d == 1:
                        changes[rand_choice(["beauty", "body", "charm", "refinement"])] -= 1

                text_changes += self.apply_changes(girl, changes)

                if girl.get_stat(self.holding, raw=True) >= girl.get_stat_minmax(self.holding, raw = True)[1]:
                    calendar.set_alarm(calendar.time+1, StoryEvent(label="farm_max_skill", type="morning", call_args=[girl, self.holding]))

                text1, text2 = girl.tire(5) #!
                descript += text1
                text_changes += text2

#                "pic is [pic]"

                if not pic:
#                    renpy.say("", "Searching girl pic for " + and_text(farm_holding_tags[self.holding]))
                    attempts = game.last_pic["attempts"]
                    pic = girl.get_pic(farm_holding_tags[self.holding], attempts=attempts, soft=True)
                if not pic:
#                    renpy.say("", "Searching farm pic")
                    attempts = game.last_pic["attempts"]
                    pic = farm.get_pic(farm_holding_tags[self.holding], attempts=attempts)

                events.append(Event(pic, char = girl.char, text = descript, changes = text_changes, type = "Farm"))

            # Updates duration

            if self.duration > 0:
                self.duration -= 1

            # Returns final list of events

            return events


        def apply_changes(self, girl, changes):

            text_changes = "\n"

            for stat, chg in changes.items():
                changes[stat] = girl.change_stat(stat, chg)

                if stat not in ("mood", "fear", "love"):
                    if changes[stat] > 0:
                        text_changes += stat_increase_dict["stat"] % (stat.capitalize(), str(round_int(changes[stat])))
                    elif changes[stat] < 0:
                        text_changes += stat_increase_dict["stat_neg"] % (stat.capitalize(), str(round_int(changes[stat])))

            return text_changes


    class Farm(object):

        def __init__(self):
            self.pens = 1
            self.installations = farm_installations
            self.girls = []
            self.default_mode = "hard"
            self.default_holding = "rest"
            self.default_resting = "intensive"

            self.programs = {}
            self.knows = {"weakness" : defaultdict(bool), "reaction" : defaultdict(list), "pos_acts" : defaultdict(list), "amb_acts" : defaultdict(list), "neg_acts" : defaultdict(list), "pos_fix" : defaultdict(list), "neg_fix" : defaultdict(list)}
            self.active = False

            self.pen_pic = Picture("pen.jpg", "brothels/farm/pen.jpg")
            unlock_pic(self.pen_pic.path)
            self.load_pics()

            self.effects = []
            self.effect_dict = defaultdict(list)

        # Effects (farm effects apply to farm girls only)

        def get_effect(self, type, target):
            return get_effect(self, type, target)

        def add_effects(self, effects, apply_boost=False, spillover=False, expires = False):
            return add_effects(self, effects, apply_boost=apply_boost, spillover=spillover, expires=expires)

        def remove_effects(self, effects):
            remove_effect(self, effects)


        def load_pics(self):
            self.pics = []

            imgfiles = [file for file in renpy.list_files() if (file.startswith("default/farm/") and is_imgfile(file))]

            # Attaching each picture to the list with appropriate tags

            for file in imgfiles:

                file_name = file.split("/")[-1]

                self.pics.append(Picture(file_name, file))

        def get_pic(self, tags, alt_tags1 = None, alt_tags2 = None, alt_tags3 = None, and_tags = None, not_tags = None, strict = False, attempts=0):
            return get_pic(self, tags=tags, alt_tags1=alt_tags1, alt_tags2=alt_tags2, alt_tags3=alt_tags3, and_tags=and_tags, not_tags=not_tags, strict=strict, attempts=attempts)

        def get_pen_limit(self):
            return brothel.get_maxbedrooms() // 2

        def get_pen_cost(self):
            return 100 * self.pens

        def has_room(self):
            if len(self.girls) < self.pens:
                return True
            return False

        def add_pen(self):
            if self.pens >= self.get_pen_limit():
                return False, "You can't expand the farm further for now. This would draw attention to us..."
            elif MC.gold < self.get_pen_cost():
                return False, "You don't have enough gold! Stop wasting my time."
            elif renpy.call_screen("yes_no", "Do you really want to add a pen to the farm for " + str(farm.get_pen_cost()) + " gold?"):
                MC.gold -= self.get_pen_cost()
                self.pens += 1
                renpy.play(s_gold, "sound")
                return True, "You've bought a new pen for the farm. It can now hold one more girl."
            else:
                return False, ""

        def upgrade(self, inst): # Where inst is an object
            return inst.upgrade()

        def send_girl(self, girl, program):
            girl.work_whore = False
            if girl in MC.girls:
                MC.girls.remove(girl)
                if MC.girls:
                    selected_girl = MC.girls[0]
                else:
                    selected_girl = None
            if girl in brothel.master_bedroom.girls:
                brothel.master_bedroom.remove_girl(girl)
            if girl not in self.girls:
                self.girls.append(girl)
            self.change_program(girl, program)

        def remove_girl(self, girl):
            if girl not in MC.girls:
                MC.girls.append(girl)
            if girl in self.girls:
                self.girls.remove(girl)
#             del self.programs[girl]
            self.assign_girls()

        def reset(self): # Resets all programs to default and 'evicts' girls that don't belong

            self.programs = {}

            for girl in self.girls:
                if girl in MC.girls:
                    self.remove_girl(girl)
                else:
                    self.programs[girl] = FarmProgram(girl)
                    self.programs[girl].update()

            self.assign_girls()

        def change_program(self, girl, program):
            program.update()
            self.programs[girl] = program
            self.assign_girls()

        def refresh(self):
            self.locked_girls = []
            self.unassignable = []
            self.refused = []
            self.tired = []
            for inst in self.installations.values():
                inst.refresh()
            for prog in self.programs.values():
                prog.refresh()

        def test_exit_conditions(self, girl): # returns reason if girl is ready to exit
            prog = self.programs[girl]
            if prog.duration == 0:
                return "time up"
            elif prog.condition != "none" and prog.target != "no training":
                if prog.target == "auto":
                    available_acts = [act for act in extended_sex_acts if girl.will_do_farm_act(act, prog.mode) and not compare_preference(girl, act, prog.condition)]
                    if not available_acts:
                        return "condition met"
                else:
                    if not girl.will_do_farm_act(prog.target, prog.mode) or compare_preference(girl, prog.target, prog.condition):
                        return "condition met"
            return False

        def test_resting_conditions(self, girl): # returns True if girl must rest
            if self.programs[girl].resting == "conservative":
                if self.programs[girl].act == "group" and girl.energy <= 30:
                    return True
                elif girl.energy <= 15:
                    return True

            elif self.programs[girl].resting == "intensive":
                if self.programs[girl].act == "group" and girl.energy <= 20:
                    return True
                elif girl.energy <= 10:
                    return True

            elif girl.energy <= 0:
                return True

            elif girl.hurt > 0:
                return True

            return False

        def exhaust_girl(self, girl, energy): # May hurt a girl if her energy is too low
            if energy <= -10:
                girl.get_hurt(dice(5))
            elif energy < 0:
                girl.get_hurt(dice(3))

#        def recover_girl(self, girl):

        def assign_girls(self, logging=False): # Send girls to the appropriate facility, returns 3 girl lists: training, holding (work), resting

            self.refresh()

            training_girls = []
            holding_girls = []
            resting_girls = []

            unassigned = []

            debug_report = ""

            # first round of assignation

            for girl in self.girls:

                prog = self.programs[girl]

                # Auto-resting test

                if farm.test_resting_conditions(girl):
                    prog.tired = True
                    resting_girls.append(girl)
                    if logging: log.add_report(girl.fullname + " was too tired and Gizel sent her to rest (resting mode: " + self.programs[girl].resting + ").")
#                    renpy.say(girl.name + " is too tired")

                # Holding girls

                elif prog.target == "no training" and prog.holding == "rest":
                    resting_girls.append(girl)

                elif prog.target == "no training":
                    holding_girls.append(girl)

                # Training girls

                else:

                    # Assign training

                    if self.assign_training(girl):

                        # Assign preferred facility if exists

                        if prog.installation and not prog.auto_inst:
                            prog.installation.girls.append(girl)
                            if logging: log.add_report("As per her training program, " + girl.fullname + " was assigned to the " + prog.installation.name)
                        elif prog.avoid_weakness: # Assigns to another installation if has been ordered to by the player
                            for inst in renpy.random.sample(self.installations.values(), len(self.installations.values())):
                                if inst != self.installations[self.knows["weakness"][girl]] and inst.count_free_minions() > 0:
                                    prog.installation = inst
                                    inst.girls.append(girl)
                                    break
                            else:
                                unassigned.append(girl)
                        elif self.knows["weakness"][girl] and not girl.get_effect("special", "all farm weaknesses"):
                            # Assigns to an installation corresponding to her weakness if known and auto on
#                            renpy.say("", "Farm knows " + girl.name + " is weak to " + self.knows["weakness"].name)
                            prog.installation = self.installations[self.knows["weakness"][girl]]
                            self.installations[self.knows["weakness"][girl]].girls.append(girl)
                            if logging: log.add_report(girl.fullname + " was assigned to the " + prog.installation.name + " because Gizel knows she is weak to " + self.knows["weakness"][girl] + "s.")
                        else:
#                            renpy.say("", "Farm doesn't know " + girl.name + " 's weakness.")
                            unassigned.append(girl)

                    # Refused training

                    elif prog.holding == "rest":
                        resting_girls.append(girl)
                        if logging: log.add_report(girl.fullname + " refused training and was assigned to rest.")
                    else:
                        holding_girls.append(girl)
                        if logging: log.add_report(girl.fullname + " refused training and was assigned to work.")

            for inst in self.installations.values():
                excess_girls = inst.assign_minions() # Returns excess girls to be assigned elsewhere automatically

                if logging:
                    for girl in excess_girls:
                        log.add_report(girl.fullname + " couldn't train in the " + inst.name + " because there were not enough available minions.")

                unassigned += excess_girls

#            debug_report += "Unassigned: " + and_text([g.name for g in unassigned])

            # Second round of assignation

            renpy.random.shuffle(unassigned)

            for girl in unassigned:
                prog = self.programs[girl]
                for inst in renpy.random.sample(self.installations.values(), len(self.installations.values())):
                    if inst.count_free_minions() > 0 and prog.act != "group":
                        prog.installation = inst
                        inst.girls.append(girl)
                        inst.assign_minions()
                        if logging: log.add_report(girl.fullname + " was assigned to train in the " + inst.name + ".")
                        break
                    elif inst.count_free_minions() > 1:
                        prog.installation = inst
                        inst.girls.append(girl)
                        inst.assign_minions()
                        if logging: log.add_report(girl.fullname + " was assigned to train in the " + inst.name + ".")
                        break



            for inst in self.installations.values():
#                renpy.say("", inst.name + " has girls: " + and_text([g.name for g in inst.girls]))
                for girl in inst.girls:
                    training_girls.append(girl)

            # Final assignation

            for girl in self.girls:
                prog = self.programs[girl]

                if girl not in (training_girls + holding_girls + resting_girls):

                    prog.inst_full = True

                    if prog.holding == "rest":
                        resting_girls.append(girl)
                        if logging: log.add_report(girl.fullname + " couldn't train in a free facility and was assigned to rest.")
                    else:
                        holding_girls.append(girl)
                        if logging: log.add_report(girl.fullname + " couldn't train in a free facility and was assigned to work.")

#            if debug_mode:
#                debug_report += "\nIn training: " + and_text([g.name for g in training_girls]) + "\nHolding: " + and_text([g.name for g in holding_girls]) + "\nResting: " + and_text([g.name for g in resting_girls])
#                renpy.say("", debug_report)

            return training_girls, holding_girls, resting_girls

        def assign_training(self, girl): # Assigns an 'act' to train for the night. Returns False if impossible.

#            renpy.say("", "Assigning training to " + girl.name)

            prog = self.programs[girl]

            if prog.target == "no training":
                prog.act = None
                if debug_mode:
                    renpy.say("", "WRONG: not in training")
                return False
            elif prog.target != "auto":
                prog.act = prog.target
                return True
            else: # Auto assign
                available_acts = []
                maybe = []

                for act in extended_sex_acts:
                    if girl.will_do_farm_act(act, self.programs[girl].mode):

                        # Checks if has already reached condition (the act then becomes less of a priority)

                        if self.programs[girl].condition == "none":
                            available_acts.append(act)
                        else:
                            if compare_preference(girl, act, self.programs[girl].condition):
                                maybe.append(act)
                            else:
                                available_acts.append(act)

                if available_acts:
                    self.programs[girl].act = rand_choice(available_acts)
                    return True
                elif maybe:
                    self.programs[girl].act = rand_choice(maybe)
                    return True
                else:
                    self.programs[girl].act = None
                    prog.refused = True
#                    if debug_mode:
#                        renpy.say("", "Refused all training")
                    return False

        def count_minions(self):
            _min = 0
            for inst in self.installations.values():
                _min += len(inst.minions)

            return _min

        def get_minions(self, type):

            return self.installations[farm_installations_dict[type]].minions

        def get_hurt_minions(self):

            minions = []

            for inst in self.installations.values():
                minions += inst.get_hurt_minions()

            return minions

        def hurt_minions(self): # Runs every turn to reduce minions health until they retire

            retired = []

            for inst in self.installations.values():
                for mn in inst.get_hurt_minions():
                    mn.hp -= 1

                    if mn.hp <= 0:
                        inst.minions.remove(mn)
                        retired.append(mn)

            return retired

        def remove_minion(self, mn):
            self.installations[farm_installations_dict[mn.type]].minions.remove(mn)

#         def add_girl(self, girl):

#             if len(self.girls) < self.pens and girl not in self.girls:
#                 self.girls.append(girl)

#                 if not gisele.knows[girl]:
#                     gisele.knows[girl] = defaultdict(bool)

#             else:
#                 renpy.say(gizel, "Well, it seems that all the pens are full at the moment.")

#                 if len(self.pens) < self.pen_limit:
#                     if self.add_pen() and girl not in self.girls:
#                         self.add_girl(girl)

#             return False

#        def remove_girl(self, girl):

#            if girl in self.girls:
#                self.girls.remove(girl)
#                return True
#            else:
#                raise AssertionError, girl.name + " not found in farm"
##                return False

        def add_minion(self, minion):
            inst = self.installations[farm_installations_dict[minion.type]]
            return inst.add_minion(minion)

        def remove_minion(self, minion):
            for installation in self.installations.values():
                if minion in installation.minions:
                    installation.minions.remove(minion)
                    return True
            else:
                raise AssertionError, minion.name + " not found in farm"
                return False

#        def get_free_minions(self):

#            free_minions = [mn for mn in self.minions if mn.free]

#            return free_minions

#        def get_available_minion(self, program, type=None):

#            # Get the best available minion (if provided, a given type is chosen)

#            free_minions = self.get_free_minions()

#            if free_minions:
#                free_minions.sort(key = lambda x: x.score_me(program, type), reverse = True)
#                return free_minions[0]

#            return None

#### END OF BK FARM FILE ####
