class Entry:
    def __init__(self, dept, in_time, out_time, duration="", flag=0):
        self.dept = dept
        self.inTime = in_time
        self.outTime = out_time
        self.duration = duration
        self.flag = flag
