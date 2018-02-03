class Entry:
    def __init__(self,dept,inTime,outTime,duration="",flag=0):
        self.dept = dept
        self.inTime = inTime
        self.outTime = outTime
        self.duration = duration
        self.flag = flag