nums_and_words = [(1, 'one'), (2, 'two'), (3, 'three')]
z = zip
z(*nums_and_words)
nums, words = zip(*nums_and_words)
print(nums)