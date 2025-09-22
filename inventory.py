class PlayerInventory:
    def __init__(self):
        self.slots = [None] * 36 # 9 hotbar slots + 27 inventory slots
        self.armor_slot = None # A single slot for a chestplate
        self.max_stack_size = 99999 # Effectively infinite

    def has_item(self, item_type, count=1):
        """Checks if the inventory contains at least a certain count of an item."""
        total_count = 0
        for slot in self.slots:
            if slot and slot['type'] == item_type:
                total_count += slot['count']
        return total_count >= count

    def remove_item(self, item_type, count=1):
        """Removes a given number of items from the inventory, starting from the end."""
        remaining_to_remove = count
        # Iterate backwards to remove from the end of inventory first (non-hotbar)
        for i in range(len(self.slots) - 1, -1, -1):
            slot = self.slots[i]
            if slot and slot['type'] == item_type:
                remove_amount = min(remaining_to_remove, slot['count'])
                slot['count'] -= remove_amount
                remaining_to_remove -= remove_amount

                if slot['count'] <= 0:
                    self.slots[i] = None

                if remaining_to_remove <= 0:
                    return True
        return False # Not enough items were found to remove

    def get_slot(self, index):
        if 0 <= index < len(self.slots):
            return self.slots[index]
        return None

    def set_slot(self, index, item):
        if 0 <= index < len(self.slots):
            self.slots[index] = item

    def can_add_item(self, item_type, count):
        """Checks if a given number of items can be added to the inventory without actually adding them."""
        remaining_count = count
        
        # Check how much can be added to existing stacks
        for slot in self.slots:
            if slot and slot['type'] == item_type and slot['count'] < self.max_stack_size:
                can_add_to_stack = self.max_stack_size - slot['count']
                remaining_count -= can_add_to_stack
                if remaining_count <= 0:
                    return True
        
        # Check how much can be added to empty slots
        empty_slots = self.slots.count(None)
        if remaining_count <= empty_slots * self.max_stack_size:
            return True
            
        return False

    def add_item(self, item_type, count=1):
        # First, try to stack with existing items in both inventory and hotbar
        for i, slot in enumerate(self.slots):
            if slot and slot['type'] == item_type and slot['count'] < self.max_stack_size:
                can_add = self.max_stack_size - slot['count']
                add_amount = min(count, can_add)
                slot['count'] += add_amount
                count -= add_amount
                if count == 0:
                    return True
        
        # Next, find an empty slot (prefer hotbar, then main inventory)
        # Hotbar slots are 0-8
        for i in range(9):
            if self.slots[i] is None:
                self.slots[i] = {'type': item_type, 'count': count}
                return True
        # Main inventory slots are 9-35
        for i in range(9, len(self.slots)):
            if self.slots[i] is None:
                self.slots[i] = {'type': item_type, 'count': count}
                return True
        
        return False # Inventory is full