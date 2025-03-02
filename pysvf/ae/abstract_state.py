from typing import Dict, Set, Optional, List, Tuple, Union
from enum import Enum
import sys

class IntervalValue:
    """Python implementation of interval value for abstract interpretation."""
    
    def __init__(self, lb: int = None, ub: int = None):
        """Create an interval [lb, ub]. None for lb means negative infinity, None for ub means positive infinity."""
        self._lb = lb
        self._ub = ub
    
    @staticmethod
    def top():
        """Create a top ([-∞,+∞]) interval."""
        return IntervalValue(None, None)
    
    @staticmethod
    def bottom():
        """Create a bottom (⊥) interval."""
        # Represent bottom as an invalid interval where lb > ub
        return IntervalValue(1, 0)
    
    def is_top(self) -> bool:
        """Check if this is a top interval."""
        return self._lb is None and self._ub is None
    
    def is_bottom(self) -> bool:
        """Check if this is a bottom interval."""
        if self._lb is None or self._ub is None:
            return False
        return self._lb > self._ub
    
    def set_to_top(self) -> None:
        """Set this interval to top."""
        self._lb = None
        self._ub = None
    
    def set_to_bottom(self) -> None:
        """Set this interval to bottom."""
        self._lb = 1
        self._ub = 0
    
    def contain(self, other: 'IntervalValue') -> bool:
        """Check if this interval contains another interval."""
        if self.is_bottom():
            return False
        if other.is_bottom():
            return True
        
        # Check lower bound
        if self._lb is None:  # -∞
            lb_ok = True
        elif other._lb is None:  # -∞
            lb_ok = False
        else:
            lb_ok = self._lb <= other._lb
        
        # Check upper bound
        if self._ub is None:  # +∞
            ub_ok = True
        elif other._ub is None:  # +∞
            ub_ok = False
        else:
            ub_ok = self._ub >= other._ub
        
        return lb_ok and ub_ok
    
    def join(self, other: 'IntervalValue') -> 'IntervalValue':
        """Join with another interval (least upper bound)."""
        if self.is_bottom():
            return IntervalValue(other._lb, other._ub)
        if other.is_bottom():
            return IntervalValue(self._lb, self._ub)
        
        # Calculate new lower bound
        if self._lb is None or other._lb is None:
            new_lb = None
        else:
            new_lb = min(self._lb, other._lb)
        
        # Calculate new upper bound
        if self._ub is None or other._ub is None:
            new_ub = None
        else:
            new_ub = max(self._ub, other._ub)
        
        return IntervalValue(new_lb, new_ub)
    
    def meet(self, other: 'IntervalValue') -> 'IntervalValue':
        """Meet with another interval (greatest lower bound)."""
        if self.is_bottom() or other.is_bottom():
            return IntervalValue.bottom()
        
        # Calculate new lower bound
        if self._lb is None:
            new_lb = other._lb
        elif other._lb is None:
            new_lb = self._lb
        else:
            new_lb = max(self._lb, other._lb)
        
        # Calculate new upper bound
        if self._ub is None:
            new_ub = other._ub
        elif other._ub is None:
            new_ub = self._ub
        else:
            new_ub = min(self._ub, other._ub)
        
        # Check if result is bottom
        if new_lb is not None and new_ub is not None and new_lb > new_ub:
            return IntervalValue.bottom()
        
        return IntervalValue(new_lb, new_ub)
    
    def widening(self, other: 'IntervalValue') -> 'IntervalValue':
        """Widen this interval with another interval."""
        if self.is_bottom():
            return IntervalValue(other._lb, other._ub)
        if other.is_bottom():
            return IntervalValue(self._lb, self._ub)
        
        # Calculate new lower bound
        if self._lb is None:
            new_lb = None
        elif other._lb is None:
            new_lb = None
        elif other._lb < self._lb:
            new_lb = None  # Widening to -∞
        else:
            new_lb = self._lb
        
        # Calculate new upper bound
        if self._ub is None:
            new_ub = None
        elif other._ub is None:
            new_ub = None
        elif other._ub > self._ub:
            new_ub = None  # Widening to +∞
        else:
            new_ub = self._ub
        
        return IntervalValue(new_lb, new_ub)
    
    def narrowing(self, other: 'IntervalValue') -> 'IntervalValue':
        """Narrow this interval with another interval."""
        if self.is_bottom() or other.is_bottom():
            return IntervalValue.bottom()
        
        # Calculate new lower bound
        if self._lb is None and other._lb is not None:
            new_lb = other._lb
        else:
            new_lb = self._lb
        
        # Calculate new upper bound
        if self._ub is None and other._ub is not None:
            new_ub = other._ub
        else:
            new_ub = self._ub
        
        return IntervalValue(new_lb, new_ub)
    
    def equals(self, other: 'IntervalValue') -> bool:
        """Check if this interval equals another interval."""
        if self.is_bottom() and other.is_bottom():
            return True
        if self.is_bottom() or other.is_bottom():
            return False
        
        return (self._lb == other._lb and self._ub == other._ub)
    
    def __str__(self) -> str:
        if self.is_bottom():
            return "⊥"
        
        lb_str = "-∞" if self._lb is None else str(self._lb)
        ub_str = "+∞" if self._ub is None else str(self._ub)
        return f"[{lb_str}, {ub_str}]"
    
    def __repr__(self) -> str:
        return self.__str__()


class AddressValue:
    """Python implementation of address value for abstract interpretation."""
    
    # The high byte for virtual addresses (0x7F000000)
    _ADDR_HIGH_BYTE = 0x7F000000
    _ADDR_MASK = 0xFF000000
    
    def __init__(self, addresses: Set[int] = None):
        """Initialize with a set of addresses."""
        self._addrs = addresses if addresses is not None else set()
    
    @staticmethod
    def getVirtualMemAddress(idx: int) -> int:
        """Convert an internal index to a virtual memory address."""
        return AddressValue._ADDR_HIGH_BYTE | idx
    
    @staticmethod
    def isVirtualMemAddress(val: int) -> bool:
        """Check if value is a virtual memory address."""
        return (val & AddressValue._ADDR_MASK) == AddressValue._ADDR_HIGH_BYTE
    
    @staticmethod
    def getInternalID(idx: int) -> int:
        """Return the internal index if idx is an address, otherwise return idx."""
        if AddressValue.isVirtualMemAddress(idx):
            return idx & ~AddressValue._ADDR_MASK
        return idx
    
    def get_addrs(self) -> Set[int]:
        """Get the set of addresses."""
        return self._addrs
    
    def contains_addr(self, addr: int) -> bool:
        """Check if a specific address is contained."""
        return addr in self._addrs
    
    def add_addr(self, addr: int) -> None:
        """Add an address to the set."""
        self._addrs.add(addr)
    
    def join(self, other: 'AddressValue') -> 'AddressValue':
        """Join with another address value."""
        result = self._addrs.union(other._addrs)
        return AddressValue(result)
    
    def meet(self, other: 'AddressValue') -> 'AddressValue':
        """Meet with another address value."""
        result = self._addrs.intersection(other._addrs)
        return AddressValue(result)
    
    def equals(self, other: 'AddressValue') -> bool:
        """Check if equals to another address value."""
        return self._addrs == other._addrs
    
    def __str__(self) -> str:
        if not self._addrs:
            return "∅"
        addr_strs = [hex(addr) for addr in sorted(self._addrs)]
        return "{" + ", ".join(addr_strs) + "}"
    
    def __repr__(self) -> str:
        return self.__str__()


class AbstractValueType(Enum):
    """Type of abstract value."""
    INTERVAL = 0
    ADDRESS = 1


class AbstractValue:
    """Python implementation of abstract value that can be either an interval or a set of addresses."""
    
    def __init__(self):
        """Initialize as bottom."""
        self._type = None
        self._interval = None
        self._address = None
    
    @staticmethod
    def createInterval(lb: int = None, ub: int = None) -> 'AbstractValue':
        """Create an abstract value containing an interval."""
        val = AbstractValue()
        val._type = AbstractValueType.INTERVAL
        val._interval = IntervalValue(lb, ub)
        return val
    
    @staticmethod
    def createAddress(addresses: Set[int] = None) -> 'AbstractValue':
        """Create an abstract value containing a set of addresses."""
        val = AbstractValue()
        val._type = AbstractValueType.ADDRESS
        val._address = AddressValue(addresses)
        return val
    
    def isInterval(self) -> bool:
        """Check if this is an interval value."""
        return self._type == AbstractValueType.INTERVAL
    
    def isAddr(self) -> bool:
        """Check if this is an address value."""
        return self._type == AbstractValueType.ADDRESS
    
    def getInterval(self) -> IntervalValue:
        """Get the interval value."""
        assert self.isInterval(), "Not an interval value"
        return self._interval
    
    def getAddress(self) -> AddressValue:
        """Get the address value."""
        assert self.isAddr(), "Not an address value"
        return self._address
    
    def join(self, other: 'AbstractValue') -> 'AbstractValue':
        """Join with another abstract value."""
        if self.isInterval() and other.isInterval():
            result = AbstractValue()
            result._type = AbstractValueType.INTERVAL
            result._interval = self._interval.join(other._interval)
            return result
        elif self.isAddr() and other.isAddr():
            result = AbstractValue()
            result._type = AbstractValueType.ADDRESS
            result._address = self._address.join(other._address)
            return result
        else:
            raise ValueError("Cannot join values of different types")
    
    def meet(self, other: 'AbstractValue') -> 'AbstractValue':
        """Meet with another abstract value."""
        if self.isInterval() and other.isInterval():
            result = AbstractValue()
            result._type = AbstractValueType.INTERVAL
            result._interval = self._interval.meet(other._interval)
            return result
        elif self.isAddr() and other.isAddr():
            result = AbstractValue()
            result._type = AbstractValueType.ADDRESS
            result._address = self._address.meet(other._address)
            return result
        else:
            raise ValueError("Cannot meet values of different types")
    
    def equals(self, other: 'AbstractValue') -> bool:
        """Check if equals to another abstract value."""
        if self._type != other._type:
            return False
        
        if self.isInterval():
            return self._interval.equals(other._interval)
        else:  # isAddr()
            return self._address.equals(other._address)
    
    def __str__(self) -> str:
        if self.isInterval():
            return str(self._interval)
        elif self.isAddr():
            return str(self._address)
        else:
            return "undefined"
    
    def __repr__(self) -> str:
        return self.__str__()


class AbstractState:
    """Python implementation of abstract state for abstract interpretation."""
    
    def __init__(self, var_to_val: Dict[int, AbstractValue] = None, addr_to_val: Dict[int, AbstractValue] = None):
        """Initialize the abstract state."""
        self._varToAbsVal = var_to_val if var_to_val is not None else {}
        self._addrToAbsVal = addr_to_val if addr_to_val is not None else {}
    
    def bottom(self) -> 'AbstractState':
        """Create a copy of this state with all interval values set to bottom."""
        inv = AbstractState(self._varToAbsVal.copy(), self._addrToAbsVal.copy())
        for item_key in inv._varToAbsVal:
            if inv._varToAbsVal[item_key].isInterval():
                inv._varToAbsVal[item_key].getInterval().set_to_bottom()
        return inv
    
    def top(self) -> 'AbstractState':
        """Create a copy of this state with all interval values set to top."""
        inv = AbstractState(self._varToAbsVal.copy(), self._addrToAbsVal.copy())
        for item_key in inv._varToAbsVal:
            if inv._varToAbsVal[item_key].isInterval():
                inv._varToAbsVal[item_key].getInterval().set_to_top()
        return inv
    
    def sliceState(self, ids: Set[int]) -> 'AbstractState':
        """Copy some values specified by ids and return a new AbstractState."""
        inv = AbstractState()
        for id in ids:
            if id in self._varToAbsVal:
                inv._varToAbsVal[id] = self._varToAbsVal[id]
        return inv
    
    def __getitem__(self, var_id: int) -> AbstractValue:
        """Get abstract value of variable."""
        return self._varToAbsVal.get(var_id, AbstractValue.createInterval())
    
    def inVarToAddrsTable(self, id: int) -> bool:
        """Check if variable is in varToAddrs table."""
        return id in self._varToAbsVal and self._varToAbsVal[id].isAddr()
    
    def inVarToValTable(self, id: int) -> bool:
        """Check if variable is in varToVal table."""
        return id in self._varToAbsVal and self._varToAbsVal[id].isInterval()
    
    def inAddrToAddrsTable(self, id: int) -> bool:
        """Check if memory address stores memory addresses."""
        return id in self._addrToAbsVal and self._addrToAbsVal[id].isAddr()
    
    def inAddrToValTable(self, id: int) -> bool:
        """Check if memory address stores abstract value."""
        return id in self._addrToAbsVal and self._addrToAbsVal[id].isInterval()
    
    def getVarToVal(self) -> Dict[int, AbstractValue]:
        """Get var2val map."""
        return self._varToAbsVal
    
    def getLocToVal(self) -> Dict[int, AbstractValue]:
        """Get loc2val map."""
        return self._addrToAbsVal
    
    def widening(self, other: 'AbstractState') -> 'AbstractState':
        """Domain widen with other, and return the widened domain."""
        result = AbstractState()
        
        # Handle _varToAbsVal
        all_var_keys = set(self._varToAbsVal.keys()).union(other._varToAbsVal.keys())
        for key in all_var_keys:
            if key in self._varToAbsVal and key in other._varToAbsVal:
                if self._varToAbsVal[key].isInterval() and other._varToAbsVal[key].isInterval():
                    # Both intervals - apply widening
                    new_val = AbstractValue.createInterval()
                    new_val._interval = self._varToAbsVal[key].getInterval().widening(
                        other._varToAbsVal[key].getInterval())
                    result._varToAbsVal[key] = new_val
                elif self._varToAbsVal[key].isAddr() and other._varToAbsVal[key].isAddr():
                    # Both address sets - use union
                    new_val = AbstractValue.createAddress()
                    new_val._address = self._varToAbsVal[key].getAddress().join(
                        other._varToAbsVal[key].getAddress())
                    result._varToAbsVal[key] = new_val
            elif key in self._varToAbsVal:
                result._varToAbsVal[key] = self._varToAbsVal[key]
            else:  # key in other._varToAbsVal
                result._varToAbsVal[key] = other._varToAbsVal[key]
        
        # Handle _addrToAbsVal (similar logic)
        all_addr_keys = set(self._addrToAbsVal.keys()).union(other._addrToAbsVal.keys())
        for key in all_addr_keys:
            if key in self._addrToAbsVal and key in other._addrToAbsVal:
                if self._addrToAbsVal[key].isInterval() and other._addrToAbsVal[key].isInterval():
                    # Both intervals - apply widening
                    new_val = AbstractValue.createInterval()
                    new_val._interval = self._addrToAbsVal[key].getInterval().widening(
                        other._addrToAbsVal[key].getInterval())
                    result._addrToAbsVal[key] = new_val
                elif self._addrToAbsVal[key].isAddr() and other._addrToAbsVal[key].isAddr():
                    # Both address sets - use union
                    new_val = AbstractValue.createAddress()
                    new_val._address = self._addrToAbsVal[key].getAddress().join(
                        other._addrToAbsVal[key].getAddress())
                    result._addrToAbsVal[key] = new_val
            elif key in self._addrToAbsVal:
                result._addrToAbsVal[key] = self._addrToAbsVal[key]
            else:  # key in other._addrToAbsVal
                result._addrToAbsVal[key] = other._addrToAbsVal[key]
        
        return result
    
    def narrowing(self, other: 'AbstractState') -> 'AbstractState':
        """Domain narrow with other, and return the narrowed domain."""
        result = AbstractState()
        
        # Handle _varToAbsVal
        all_var_keys = set(self._varToAbsVal.keys()).union(other._varToAbsVal.keys())
        for key in all_var_keys:
            if key in self._varToAbsVal and key in other._varToAbsVal:
                if self._varToAbsVal[key].isInterval() and other._varToAbsVal[key].isInterval():
                    # Both intervals - apply narrowing
                    new_val = AbstractValue.createInterval()
                    new_val._interval = self._varToAbsVal[key].getInterval().narrowing(
                        other._varToAbsVal[key].getInterval())
                    result._varToAbsVal[key] = new_val
                elif self._varToAbsVal[key].isAddr() and other._varToAbsVal[key].isAddr():
                    # Both address sets - use intersection
                    new_val = AbstractValue.createAddress()
                    new_val._address = self._varToAbsVal[key].getAddress().meet(
                        other._varToAbsVal[key].getAddress())
                    result._varToAbsVal[key] = new_val
            elif key in self._varToAbsVal:
                result._varToAbsVal[key] = self._varToAbsVal[key]
            else:  # key in other._varToAbsVal
                result._varToAbsVal[key] = other._varToAbsVal[key]
        
        # Handle _addrToAbsVal (similar logic)
        all_addr_keys = set(self._addrToAbsVal.keys()).union(other._addrToAbsVal.keys())
        for key in all_addr_keys:
            if key in self._addrToAbsVal and key in other._addrToAbsVal:
                if self._addrToAbsVal[key].isInterval() and other._addrToAbsVal[key].isInterval():
                    # Both intervals - apply narrowing
                    new_val = AbstractValue.createInterval()
                    new_val._interval = self._addrToAbsVal[key].getInterval().narrowing(
                        other._addrToAbsVal[key].getInterval())
                    result._addrToAbsVal[key] = new_val
                elif self._addrToAbsVal[key].isAddr() and other._addrToAbsVal[key].isAddr():
                    # Both address sets - use intersection
                    new_val = AbstractValue.createAddress()
                    new_val._address = self._addrToAbsVal[key].getAddress().meet(
                        other._addrToAbsVal[key].getAddress())
                    result._addrToAbsVal[key] = new_val
            elif key in self._addrToAbsVal:
                result._addrToAbsVal[key] = self._addrToAbsVal[key]
            else:  # key in other._addrToAbsVal
                result._addrToAbsVal[key] = other._addrToAbsVal[key]
        
        return result
    
    def joinWith(self, other: 'AbstractState') -> None:
        """Join this state with another state, modifying this state."""
        # Process varToAbsVal map
        for key, value in other._varToAbsVal.items():
            if key in self._varToAbsVal:
                new_val = self._varToAbsVal[key].join(value)
                self._varToAbsVal[key] = new_val
            else:
                # Copy the value
                if value.isInterval():
                    self._varToAbsVal[key] = AbstractValue.createInterval()
                    self._varToAbsVal[key]._interval = value.getInterval()
                else:  # isAddr()
                    self._varToAbsVal[key] = AbstractValue.createAddress()
                    self._varToAbsVal[key]._address = value.getAddress()
        
        # Process addrToAbsVal map with the same logic
        for key, value in other._addrToAbsVal.items():
            if key in self._addrToAbsVal:
                new_val = self._addrToAbsVal[key].join(value)
                self._addrToAbsVal[key] = new_val
            else:
                # Copy the value
                if value.isInterval():
                    self._addrToAbsVal[key] = AbstractValue.createInterval()
                    self._addrToAbsVal[key]._interval = value.getInterval()
                else:  # isAddr()
                    self._addrToAbsVal[key] = AbstractValue.createAddress()
                    self._addrToAbsVal[key]._address = value.getAddress()
    
    def meetWith(self, other: 'AbstractState') -> None:
        """Meet this state with other state, modifying this state."""
        # Handle _varToAbsVal
        keys_to_remove = []
        for key in self._varToAbsVal:
            if key in other._varToAbsVal:
                if self._varToAbsVal[key].isInterval() and other._varToAbsVal[key].isInterval():
                    # Both intervals - apply meet
                    new_interval = self._varToAbsVal[key].getInterval().meet(
                        other._varToAbsVal[key].getInterval())
                    self._varToAbsVal[key] = AbstractValue.createInterval()
                    self._varToAbsVal[key]._interval = new_interval
                    if new_interval.is_bottom():
                        keys_to_remove.append(key)
                elif self._varToAbsVal[key].isAddr() and other._varToAbsVal[key].isAddr():
                    # Both address sets - use intersection
                    new_address = self._varToAbsVal[key].getAddress().meet(
                        other._varToAbsVal[key].getAddress())
                    self._varToAbsVal[key] = AbstractValue.createAddress()
                    self._varToAbsVal[key]._address = new_address
                    if not new_address.get_addrs():  # Empty set
                        keys_to_remove.append(key)
            else:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._varToAbsVal[key]
        
        # Handle _addrToAbsVal (similar logic)
        keys_to_remove = []
        for key in self._addrToAbsVal:
            if key in other._addrToAbsVal:
                if self._addrToAbsVal[key].isInterval() and other._addrToAbsVal[key].isInterval():
                    # Both intervals - apply meet
                    new_interval = self._addrToAbsVal[key].getInterval().meet(
                        other._addrToAbsVal[key].getInterval())
                    self._addrToAbsVal[key] = AbstractValue.createInterval()
                    self._addrToAbsVal[key]._interval = new_interval
                    if new_interval.is_bottom():
                        keys_to_remove.append(key)
                elif self._addrToAbsVal[key].isAddr() and other._addrToAbsVal[key].isAddr():
                    # Both address sets - use intersection
                    new_address = self._addrToAbsVal[key].getAddress().meet(
                        other._addrToAbsVal[key].getAddress())
                    self._addrToAbsVal[key] = AbstractValue.createAddress()
                    self._addrToAbsVal[key]._address = new_address
                    if not new_address.get_addrs():  # Empty set
                        keys_to_remove.append(key)
            else:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._addrToAbsVal[key]
    
    def store(self, addr: int, val: AbstractValue) -> None:
        """Store a value to a memory address."""
        assert AddressValue.isVirtualMemAddress(addr), "Not a virtual address"
        if AddressValue.getInternalID(addr) == 0:  # null pointer
            return
        obj_id = AddressValue.getInternalID(addr)
        self._addrToAbsVal[obj_id] = val
    
    def load(self, addr: int) -> AbstractValue:
        """Load a value from a memory address."""
        assert AddressValue.isVirtualMemAddress(addr), "Not a virtual address"
        obj_id = AddressValue.getInternalID(addr)
        if obj_id in self._addrToAbsVal:
            return self._addrToAbsVal[obj_id]
        # Return a default empty value if address not found
        return AbstractValue.createInterval()
    
    def equals(self, other: 'AbstractState') -> bool:
        """Check if this state equals another state."""
        return self._eqVarToValMap(self._varToAbsVal, other._varToAbsVal) and \
               self._eqVarToValMap(self._addrToAbsVal, other._addrToAbsVal)
    
    def _eqVarToValMap(self, lhs: Dict[int, AbstractValue], rhs: Dict[int, AbstractValue]) -> bool:
        """Helper to check if two maps are equal."""
        if len(lhs) != len(rhs):
            return False
        
        for key, value in lhs.items():
            if key not in rhs:
                return False
            if not value.equals(rhs[key]):
                return False
        
        return True
    
    def __eq__(self, other: 'AbstractState') -> bool:
        return self.equals(other)
    
    def __ne__(self, other: 'AbstractState') -> bool:
        return not self.equals(other)
    
    def __ge__(self, other: 'AbstractState') -> bool:
        """Check if this state contains other state (self >= other)."""
        # Check _varToAbsVal
        for key, value in other._varToAbsVal.items():
            if key not in self._varToAbsVal:
                return False
            
            self_val = self._varToAbsVal[key]
            
            if value.isInterval() and self_val.isInterval():
                if not self_val.getInterval().contain(value.getInterval()):
                    return False
            elif value.isAddr() and self_val.isAddr():
                # For address sets, check that all addresses in other are in self
                other_addrs = value.getAddress().get_addrs()
                self_addrs = self_val.getAddress().get_addrs()
                if not other_addrs.issubset(self_addrs):
                    return False
            else:
                return False  # Different types
        
        # Check _addrToAbsVal with same logic
        for key, value in other._addrToAbsVal.items():
            if key not in self._addrToAbsVal:
                return False
            
            self_val = self._addrToAbsVal[key]
            
            if value.isInterval() and self_val.isInterval():
                if not self_val.getInterval().contain(value.getInterval()):
                    return False
            elif value.isAddr() and self_val.isAddr():
                other_addrs = value.getAddress().get_addrs()
                self_addrs = self_val.getAddress().get_addrs()
                if not other_addrs.issubset(self_addrs):
                    return False
            else:
                return False  # Different types
        
        return True
    
    def __lt__(self, other: 'AbstractState') -> bool:
        return not (self >= other)
    
    def printAbstractState(self) -> None:
        """Print the abstract state."""
        print("Variable to Abstract Value Map:")
        for var_id, value in sorted(self._varToAbsVal.items()):
            print(f"  {var_id}: {value}")
        
        print("Address to Abstract Value Map:")
        for addr, value in sorted(self._addrToAbsVal.items()):
            print(f"  {addr} ({hex(AddressValue.getVirtualMemAddress(addr))}): {value}")
    
    def clear(self) -> None:
        """Clear the abstract state."""
        self._varToAbsVal.clear()
        self._addrToAbsVal.clear()
    
    # The following methods would typically interact with SVF C++ API
    # We'll provide stub implementations for these
    
    def loadValue(self, var_id: int) -> AbstractValue:
        """Load a value for a variable ID."""
        return self[var_id]
    
    def storeValue(self, var_id: int, val: AbstractValue) -> None:
        """Store a value for a variable ID."""
        self._varToAbsVal[var_id] = val
    
    def getGepObjAddrs(self, pointer: int, offset: IntervalValue) -> AddressValue:
        """Get the addresses after applying a GEP operation."""
        # This is a simplified implementation
        if not self.inVarToAddrsTable(pointer):
            return AddressValue()
            
        base_addrs = self._varToAbsVal[pointer].getAddress()
        result_addrs = set()
        
        # If the offset is a constant, apply it to all base addresses
        if offset._lb is not None and offset._ub is not None and offset._lb == offset._ub:
            const_offset = offset._lb
            for addr in base_addrs.get_addrs():
                new_addr = addr + const_offset
                result_addrs.add(new_addr)
        else:
            # If offset is a range, we would need more complex handling here
            # For simplicity, we'll just add all base addresses
            result_addrs = base_addrs.get_addrs()
        
        return AddressValue(result_addrs)
    
    def initObjVar(self, obj_var) -> None:
        """Initialize an object variable in the abstract state."""
        # This would typically interact with SVF API
        pass
    
    def getElementIndex(self, gep) -> IntervalValue:
        """Get the element index from a GEP statement."""
        # This would typically interact with SVF API
        return IntervalValue(0, 0)  # Simplified
    
    def getByteOffset(self, gep) -> IntervalValue:
        """Get the byte offset from a GEP statement."""
        # This would typically interact with SVF API
        return IntervalValue(0, 0)  # Simplified
    
    def getAllocaInstByteSize(self, addr) -> int:
        """Get the byte size of an alloca instruction."""
        # This would typically interact with SVF API
        return 8  # Simplified assumption
    
    def getPointeeElement(self, id: int):
        """Get the pointee element type."""
        # This would typically interact with SVF API
        return None 