import pytest
from pysvf.ae import IntervalValue, AddressValue, AbstractValue, AbstractState

class TestIntervalValue:
    def test_initialization(self):
        # Test regular interval
        interval = IntervalValue(1, 5)
        assert interval._lb == 1
        assert interval._ub == 5
        
        # Test top interval
        top = IntervalValue.top()
        assert top._lb is None
        assert top._ub is None
        
        # Test bottom interval
        bottom = IntervalValue.bottom()
        assert bottom.is_bottom()
    
    def test_is_top_and_bottom(self):
        # Test is_top
        assert IntervalValue.top().is_top()
        assert not IntervalValue(1, 5).is_top()
        
        # Test is_bottom
        assert IntervalValue.bottom().is_bottom()
        assert not IntervalValue(1, 5).is_bottom()
        
        # Invalid interval is bottom
        assert IntervalValue(10, 5).is_bottom()
    
    def test_set_to_top_and_bottom(self):
        interval = IntervalValue(1, 5)
        
        interval.set_to_top()
        assert interval.is_top()
        
        interval.set_to_bottom()
        assert interval.is_bottom()
    
    def test_contain(self):
        # Test regular intervals
        assert IntervalValue(1, 10).contain(IntervalValue(3, 7))
        assert IntervalValue(1, 10).contain(IntervalValue(1, 10))
        assert not IntervalValue(3, 7).contain(IntervalValue(1, 10))
        
        # Test with infinite bounds
        assert IntervalValue(None, 10).contain(IntervalValue(1, 5))
        assert IntervalValue(1, None).contain(IntervalValue(5, 10))
        assert IntervalValue(None, None).contain(IntervalValue(1, 10))
        
        # Test with bottom
        assert not IntervalValue.bottom().contain(IntervalValue(1, 5))
        assert IntervalValue(1, 5).contain(IntervalValue.bottom())
    
    def test_join(self):
        # Regular join
        result = IntervalValue(1, 5).join(IntervalValue(3, 10))
        assert result._lb == 1
        assert result._ub == 10
        
        # Join with top/infinite
        result = IntervalValue(1, 5).join(IntervalValue(None, 10))
        assert result._lb is None
        assert result._ub == 10
        
        # Join with bottom
        result = IntervalValue(1, 5).join(IntervalValue.bottom())
        assert result._lb == 1
        assert result._ub == 5
        
        result = IntervalValue.bottom().join(IntervalValue(1, 5))
        assert result._lb == 1
        assert result._ub == 5
    
    def test_meet(self):
        # Regular meet
        result = IntervalValue(1, 10).meet(IntervalValue(5, 15))
        assert result._lb == 5
        assert result._ub == 10
        
        # Meet with no overlap
        result = IntervalValue(1, 5).meet(IntervalValue(6, 10))
        assert result.is_bottom()
        
        # Meet with bottom
        result = IntervalValue(1, 5).meet(IntervalValue.bottom())
        assert result.is_bottom()
    
    def test_widening(self):
        # Test widening going up
        result = IntervalValue(1, 5).widening(IntervalValue(0, 10))
        assert result._lb is None  # expands to -∞
        assert result._ub is None  # expands to +∞
        
        # Test widening stable
        result = IntervalValue(1, 10).widening(IntervalValue(2, 5))
        assert result._lb == 1
        assert result._ub == 10
        
        # Test widening with bottom
        result = IntervalValue.bottom().widening(IntervalValue(1, 5))
        assert result._lb == 1
        assert result._ub == 5
    
    def test_narrowing(self):
        # Test narrowing from top
        result = IntervalValue(None, None).narrowing(IntervalValue(1, 5))
        assert result._lb == 1
        assert result._ub == 5
        
        # Test narrowing with bottom
        result = IntervalValue.bottom().narrowing(IntervalValue(1, 5))
        assert result.is_bottom()
    
    def test_equals(self):
        # Test equal intervals
        assert IntervalValue(1, 5).equals(IntervalValue(1, 5))
        assert not IntervalValue(1, 5).equals(IntervalValue(1, 6))
        
        # Test with bottom
        assert IntervalValue.bottom().equals(IntervalValue.bottom())
        assert not IntervalValue(1, 5).equals(IntervalValue.bottom())


class TestAddressValue:
    def test_initialization(self):
        # Test empty set
        addr_val = AddressValue()
        assert len(addr_val.get_addrs()) == 0
        
        # Test with addresses
        addr_val = AddressValue({1, 2, 3})
        assert addr_val.get_addrs() == {1, 2, 3}
    
    def test_virtual_address_functions(self):
        # Test getVirtualMemAddress
        internal_id = 123
        virtual_addr = AddressValue.getVirtualMemAddress(internal_id)
        assert AddressValue.isVirtualMemAddress(virtual_addr)
        assert AddressValue.getInternalID(virtual_addr) == internal_id
        
        # Test isVirtualMemAddress
        assert not AddressValue.isVirtualMemAddress(123)
        
        # Test getInternalID for non-virtual address
        assert AddressValue.getInternalID(123) == 123
    
    def test_address_operations(self):
        addr_val = AddressValue({1, 2})
        
        # Test contains_addr
        assert addr_val.contains_addr(1)
        assert not addr_val.contains_addr(3)
        
        # Test add_addr
        addr_val.add_addr(3)
        assert addr_val.contains_addr(3)
    
    def test_join(self):
        a1 = AddressValue({1, 2})
        a2 = AddressValue({2, 3})
        
        result = a1.join(a2)
        assert result.get_addrs() == {1, 2, 3}
    
    def test_meet(self):
        a1 = AddressValue({1, 2, 3})
        a2 = AddressValue({2, 3, 4})
        
        result = a1.meet(a2)
        assert result.get_addrs() == {2, 3}
    
    def test_equals(self):
        assert AddressValue({1, 2}).equals(AddressValue({1, 2}))
        assert not AddressValue({1, 2}).equals(AddressValue({1, 3}))


class TestAbstractValue:
    def test_create_interval(self):
        val = AbstractValue.createInterval(1, 5)
        assert val.isInterval()
        assert not val.isAddr()
        assert val.getInterval()._lb == 1
        assert val.getInterval()._ub == 5
    
    def test_create_address(self):
        val = AbstractValue.createAddress({1, 2})
        assert val.isAddr()
        assert not val.isInterval()
        assert val.getAddress().get_addrs() == {1, 2}
    
    def test_join(self):
        # Test joining intervals
        a = AbstractValue.createInterval(1, 5)
        b = AbstractValue.createInterval(3, 10)
        result = a.join(b)
        assert result.isInterval()
        assert result.getInterval()._lb == 1
        assert result.getInterval()._ub == 10
        
        # Test joining addresses
        a = AbstractValue.createAddress({1, 2})
        b = AbstractValue.createAddress({2, 3})
        result = a.join(b)
        assert result.isAddr()
        assert result.getAddress().get_addrs() == {1, 2, 3}
        
        # Test joining incompatible types
        a = AbstractValue.createInterval(1, 5)
        b = AbstractValue.createAddress({1, 2})
        with pytest.raises(ValueError):
            a.join(b)
    
    def test_meet(self):
        # Test meeting intervals
        a = AbstractValue.createInterval(1, 10)
        b = AbstractValue.createInterval(5, 15)
        result = a.meet(b)
        assert result.isInterval()
        assert result.getInterval()._lb == 5
        assert result.getInterval()._ub == 10
        
        # Test meeting addresses
        a = AbstractValue.createAddress({1, 2, 3})
        b = AbstractValue.createAddress({2, 3, 4})
        result = a.meet(b)
        assert result.isAddr()
        assert result.getAddress().get_addrs() == {2, 3}
        
        # Test meeting incompatible types
        a = AbstractValue.createInterval(1, 5)
        b = AbstractValue.createAddress({1, 2})
        with pytest.raises(ValueError):
            a.meet(b)
    
    def test_equals(self):
        # Test equal intervals
        a = AbstractValue.createInterval(1, 5)
        b = AbstractValue.createInterval(1, 5)
        c = AbstractValue.createInterval(1, 6)
        assert a.equals(b)
        assert not a.equals(c)
        
        # Test equal addresses
        a = AbstractValue.createAddress({1, 2})
        b = AbstractValue.createAddress({1, 2})
        c = AbstractValue.createAddress({1, 3})
        assert a.equals(b)
        assert not a.equals(c)
        
        # Test different types
        a = AbstractValue.createInterval(1, 5)
        b = AbstractValue.createAddress({1, 2})
        assert not a.equals(b)


class TestAbstractState:
    def test_initialization(self):
        # Test empty state
        state = AbstractState()
        assert len(state._varToAbsVal) == 0
        assert len(state._addrToAbsVal) == 0
        
        # Test with initial values
        var_map = {1: AbstractValue.createInterval(1, 5)}
        addr_map = {2: AbstractValue.createAddress({3, 4})}
        state = AbstractState(var_map, addr_map)
        assert len(state._varToAbsVal) == 1
        assert len(state._addrToAbsVal) == 1
    
    def test_bottom_top(self):
        # Create state with some values
        state = AbstractState()
        state._varToAbsVal[1] = AbstractValue.createInterval(1, 5)
        state._varToAbsVal[2] = AbstractValue.createAddress({3, 4})
        
        # Test bottom
        bottom_state = state.bottom()
        assert bottom_state._varToAbsVal[1].getInterval().is_bottom()
        assert bottom_state._varToAbsVal[2].isAddr()  # Address values unchanged
        
        # Test top
        top_state = state.top()
        assert top_state._varToAbsVal[1].getInterval().is_top()
        assert top_state._varToAbsVal[2].isAddr()  # Address values unchanged
    
    def test_slice_state(self):
        state = AbstractState()
        state._varToAbsVal[1] = AbstractValue.createInterval(1, 5)
        state._varToAbsVal[2] = AbstractValue.createInterval(10, 20)
        
        # Test slicing
        sliced = state.sliceState({1})
        assert 1 in sliced._varToAbsVal
        assert 2 not in sliced._varToAbsVal
    
    def test_getitem(self):
        state = AbstractState()
        state._varToAbsVal[1] = AbstractValue.createInterval(1, 5)
        
        # Test existing key
        val = state[1]
        assert val.isInterval()
        assert val.getInterval()._lb == 1
        
        # Test non-existing key
        val = state[2]
        assert val.isInterval()
        assert val.getInterval().is_top()
    
    def test_table_checks(self):
        state = AbstractState()
        state._varToAbsVal[1] = AbstractValue.createInterval(1, 5)
        state._varToAbsVal[2] = AbstractValue.createAddress({3, 4})
        state._addrToAbsVal[5] = AbstractValue.createInterval(10, 20)
        state._addrToAbsVal[6] = AbstractValue.createAddress({7, 8})
        
        # Test inVarToValTable
        assert state.inVarToValTable(1)
        assert not state.inVarToValTable(2)
        
        # Test inVarToAddrsTable
        assert not state.inVarToAddrsTable(1)
        assert state.inVarToAddrsTable(2)
        
        # Test inAddrToValTable
        assert state.inAddrToValTable(5)
        assert not state.inAddrToValTable(6)
        
        # Test inAddrToAddrsTable
        assert not state.inAddrToAddrsTable(5)
        assert state.inAddrToAddrsTable(6)
    
    def test_widening_narrowing(self):
        # Setup states
        state1 = AbstractState()
        state1._varToAbsVal[1] = AbstractValue.createInterval(1, 5)
        state1._varToAbsVal[2] = AbstractValue.createAddress({3, 4})
        
        state2 = AbstractState()
        state2._varToAbsVal[1] = AbstractValue.createInterval(0, 10)
        state2._varToAbsVal[2] = AbstractValue.createAddress({4, 5})
        
        # Test widening
        widened = state1.widening(state2)
        assert widened._varToAbsVal[1].getInterval()._lb is None  # widened to -∞
        assert widened._varToAbsVal[1].getInterval()._ub is None  # widened to +∞
        assert widened._varToAbsVal[2].getAddress().get_addrs() == {3, 4, 5}
        
        # Test narrowing
        narrowed = state1.narrowing(state2)
        assert narrowed._varToAbsVal[1].getInterval()._lb == 1  # narrowed to minimum
        assert narrowed._varToAbsVal[1].getInterval()._ub == 5  # narrowed to minimum
        assert narrowed._varToAbsVal[2].getAddress().get_addrs() == {4}  # intersection
    
    def test_join_meet(self):
        # Setup states
        state1 = AbstractState()
        state1._varToAbsVal[1] = AbstractValue.createInterval(1, 5)
        state1._varToAbsVal[2] = AbstractValue.createAddress({3, 4})
        
        state2 = AbstractState()
        state2._varToAbsVal[1] = AbstractValue.createInterval(3, 10)
        state2._varToAbsVal[2] = AbstractValue.createAddress({4, 5})
        state2._varToAbsVal[3] = AbstractValue.createInterval(15, 20)  # unique to state2
        
        # Also test with addrToAbsVal
        state1._addrToAbsVal[100] = AbstractValue.createInterval(1, 5)
        state2._addrToAbsVal[100] = AbstractValue.createInterval(3, 10)
        state2._addrToAbsVal[200] = AbstractValue.createAddress({7, 8})  # unique to state2
        
        # Test join
        state1.joinWith(state2)
        assert state1._varToAbsVal[1].getInterval()._lb == 1
        assert state1._varToAbsVal[1].getInterval()._ub == 10
        assert state1._varToAbsVal[2].getAddress().get_addrs() == {3, 4, 5}
        assert 3 in state1._varToAbsVal  # Key only in state2 should be copied
        assert state1._addrToAbsVal[100].getInterval()._lb == 1
        assert state1._addrToAbsVal[100].getInterval()._ub == 10
        assert 200 in state1._addrToAbsVal  # Key only in state2 should be copied
        
        # Test joinWith
        state1_copy = AbstractState()
        state1_copy._varToAbsVal = {k: v for k, v in state1._varToAbsVal.items()}
        state1_copy._addrToAbsVal = {k: v for k, v in state1._addrToAbsVal.items()}
        
        # Remember original objects to test for modifications
        original_interval_id = id(state1_copy._varToAbsVal[1])
        
        state1_copy.joinWith(state2)
        
        # Check for modified values
        assert state1_copy._varToAbsVal[1].getInterval()._lb == 1
        assert state1_copy._varToAbsVal[1].getInterval()._ub == 10
        assert state1_copy._varToAbsVal[2].getAddress().get_addrs() == {3, 4, 5}
        assert 3 in state1_copy._varToAbsVal  # New key added from state2
        
        # Check address values in addrToAbsVal
        assert state1_copy._addrToAbsVal[100].getInterval()._lb == 1
        assert state1_copy._addrToAbsVal[100].getInterval()._ub == 10
        assert 200 in state1_copy._addrToAbsVal
        
        # Check that the actual objects were modified or replaced
        assert id(state1_copy._varToAbsVal[1]) != original_interval_id
        
        # Test meet
        state1.meetWith(state2)
        assert state1._varToAbsVal[1].getInterval()._lb == 3
        assert state1._varToAbsVal[1].getInterval()._ub == 5
        assert state1._varToAbsVal[2].getAddress().get_addrs() == {4}
        assert 3 not in state1._varToAbsVal  # Key only in state2 should NOT be in result
        assert state1._addrToAbsVal[100].getInterval()._lb == 3
        assert state1._addrToAbsVal[100].getInterval()._ub == 5
        assert 200 not in state1._addrToAbsVal  # Key only in state2 should NOT be in result
        
        # Test meetWith
        state1_copy = AbstractState()
        state1_copy._varToAbsVal = {k: v for k, v in state1._varToAbsVal.items()}
        state1_copy._addrToAbsVal = {k: v for k, v in state1._addrToAbsVal.items()}
        
        state1_copy.meetWith(state2)
        
        # Check for modified values
        assert state1_copy._varToAbsVal[1].getInterval()._lb == 3
        assert state1_copy._varToAbsVal[1].getInterval()._ub == 5
        assert state1_copy._varToAbsVal[2].getAddress().get_addrs() == {4}
        assert 3 not in state1_copy._varToAbsVal  # Key only in state2 should NOT be present
        
        # Check address values
        assert state1_copy._addrToAbsVal[100].getInterval()._lb == 3
        assert state1_copy._addrToAbsVal[100].getInterval()._ub == 5
        assert 200 not in state1_copy._addrToAbsVal
        
        # Test removing keys when result is bottom
        state1_fresh = AbstractState()
        state1_fresh._varToAbsVal[1] = AbstractValue.createInterval(1, 5)
        state1_fresh._addrToAbsVal[100] = AbstractValue.createInterval(1, 5)
        
        state2_fresh = AbstractState()
        state2_fresh._varToAbsVal[1] = AbstractValue.createInterval(10, 15)  # No overlap
        state2_fresh._addrToAbsVal[100] = AbstractValue.createInterval(10, 15)  # No overlap
        
        state1_fresh.meetWith(state2_fresh)
        assert 1 not in state1_fresh._varToAbsVal  # Should be removed due to bottom result
        assert 100 not in state1_fresh._addrToAbsVal  # Should be removed
    
    def test_store_load(self):
        state = AbstractState()
        
        # Create a virtual address
        addr = AddressValue.getVirtualMemAddress(123)
        val = AbstractValue.createInterval(42, 42)
        
        # Test store
        state.store(addr, val)
        assert 123 in state._addrToAbsVal
        
        # Test load
        loaded = state.load(addr)
        assert loaded.isInterval()
        assert loaded.getInterval()._lb == 42
        assert loaded.getInterval()._ub == 42
    
    def test_comparison_operators(self):
        # Setup states
        state1 = AbstractState()
        state1._varToAbsVal[1] = AbstractValue.createInterval(1, 10)
        
        state2 = AbstractState()
        state2._varToAbsVal[1] = AbstractValue.createInterval(3, 7)
        
        state3 = AbstractState()
        state3._varToAbsVal[1] = AbstractValue.createInterval(5, 15)
        
        # Test equality
        assert state1.equals(state1)
        assert not state1.equals(state2)
        
        # Test >= operator
        assert state1 >= state2  # [1,10] contains [3,7]
        assert not state2 >= state1
        assert not state1 >= state3  # [1,10] doesn't contain [5,15]
        
        # Test < operator
        assert state2 < state1
        assert not state1 < state2
    
    def test_get_object_addrs(self):
        state = AbstractState()
        
        # Setup variable pointing to addresses
        addr_val = AbstractValue.createAddress({10, 20})
        state._varToAbsVal[1] = addr_val
        
        # Test with constant offset
        offset = IntervalValue(5, 5)
        result = state.getGepObjAddrs(1, offset)
        assert result.get_addrs() == {15, 25}  # 10+5, 20+5
        
        # Test with variable offset
        offset = IntervalValue(0, 10)
        result = state.getGepObjAddrs(1, offset)
        assert result.get_addrs() == {10, 20}  # simplified implementation returns original
    
    def test_store_load_value(self):
        state = AbstractState()
        
        # Test storeValue
        val = AbstractValue.createInterval(42, 42)
        state.storeValue(100, val)
        assert 100 in state._varToAbsVal
        
        # Test loadValue
        loaded = state.loadValue(100)
        assert loaded.isInterval()
        assert loaded.getInterval()._lb == 42

if __name__ == "__main__":
    # This allows running the tests directly with `python test_abstract_state.py`
    import sys
    
    # Run all tests by default
    test_classes = [
        TestIntervalValue,
        TestAddressValue,
        TestAbstractValue,
        TestAbstractState
    ]
    
    # Allow specifying which test classes to run
    if len(sys.argv) > 1:
        requested_tests = sys.argv[1:]
        test_classes = [cls for cls in test_classes if cls.__name__ in requested_tests]
    
    # Simple test runner
    failed = False
    for test_class in test_classes:
        print(f"\nRunning tests for {test_class.__name__}:")
        
        # Find all test methods
        methods = [m for m in dir(test_class) if m.startswith('test_')]
        for method_name in methods:
            instance = test_class()
            method = getattr(instance, method_name)
            
            # Run the test method
            try:
                method()
                print(f"  ✓ {method_name}")
            except Exception as e:
                print(f"  ✗ {method_name} - FAILED: {str(e)}")
                failed = True
    
    # Exit with appropriate status code
    sys.exit(1 if failed else 0)
