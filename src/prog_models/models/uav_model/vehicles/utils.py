# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

"""
Various utility functions 
"""

# CLASSES
# ========
class ProgressBar():
    def __init__(self, n, prefix='', suffix='', decimals=1, print_length=100, fill='█', print_end = " ") -> None:
        self.n = n
        self.prefix = prefix
        self.suffix = suffix
        self.decimals = decimals
        self.print_length = print_length
        self.fill = fill
        self.print_end = print_end

    def __call__(self, iteration):
        percent = ("{0:." + str(self.decimals) + "f}").format(100 * (iteration / float(self.n)))
        filledLength = int(self.print_length * iteration // self.n)
        bar = self.fill * filledLength + '-' * (self.print_length - filledLength)
        print('\r%s |%s| %s%% %s' % (self.prefix, bar, percent, self.suffix), end = self.print_end)
        # Print New Line on Complete
        if iteration == self.n:
            print('')