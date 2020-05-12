class PlayerClass:
    profile_id_dict = {1: 'Infiltrator', 3: 'LA', 4: 'Medic', 5: 'Engineer',
                       6: 'HA',
                       7: 'MAX'}

    def __init__(self, loadout_id=0, profile_id=0, kills=0, headshots=0, hits=0, hits_forever=0, shots_fired=0,
                 shots_fired_forever=0):
        self.loadout_id = loadout_id
        self.kills = kills
        self.headshots = headshots
        self.hits = hits
        self.hits_forever = hits_forever
        self.shots_fired = shots_fired
        self.shots_fired_forever = shots_fired_forever
        self.profile_id = profile_id

        self.class_name = self.generate_class_name()

    def generate_class_name(self):
        """
        Sets and returns the class name based on the existing profile id

        :return str: The name of the class
        """
        self.class_name = self.profile_id_dict[self.profile_id]
        return self.class_name

    @staticmethod
    def loadout_to_profile_id(loadout_id):
        """
        Converts a loadout id (1-20) to a profile id (1-7)

        :param int loadout_id: The id to convert
        :return: a profile_id
        :rtype: int
        """

        if loadout_id < 8:  # NC loadouts have the same values as profiles
            return int(loadout_id)

        else:  # TR and VS are shifted over by 7
            profile_id = int(loadout_id) % 7

            # Loadouts start at 1, so MAXes are multiples of 7 starting at 7.
            # Modulo will return 0 instead of 7, so we make a special case for it
            if profile_id == 0:
                return 7

            return profile_id

    def __contains__(self, item):
        """Returns if the profile id matches the item"""
        if item == self.profile_id:
            return True

    def __str__(self):
        return "Class: %s  %d shots %d hits %d kills  %d headshots" % (
            self.class_name, self.shots_fired, self.hits, self.kills, self.headshots)

    def __repr__(self):
        return "Class: %s  %d shots %d hits %d kills  %d headshots" % (
            self.class_name, self.shots_fired, self.hits, self.kills, self.headshots)
