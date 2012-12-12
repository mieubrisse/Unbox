"""
Removes all elements in b from a in n^2 time and returns a copy of the list
 - a: List to remove elements from
 - b: List of elements to remove
 - return: Copy of a with elements removed
"""
def filterList(a, b):
    return_list = []
    for a_elem in a:
        isDuplicate = False
        for b_elem in b:
            if a_elem == b_elem:
                isDuplicate = True
                break
        if not isDuplicate:
            return_list.append(a_elem)
    return return_list
