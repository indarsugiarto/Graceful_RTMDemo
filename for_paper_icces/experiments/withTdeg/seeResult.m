%         The format of profiler data:
% '%d,%d,%d,%d,%d,%d,%f,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%f'
%         int v;            (1)
%         int pID;          (2)
%         int cpu_freq;     (3)
%         int rtr_freq;     (4)
%         int ahb_freq;     (5)
%         int nActive;      (6)
%         double temp3;     (7)
%         int cpu2;         (8)
%         int cpu3;         (9)
%         etc.. until cpu17;(23)
%         double timestamp; (24)
%d=load('profiler_Aug_23_2017-14.02.05.log');

fname = uigetfile('profiler_*.log','Open profiler data')
if fname==0
    return
end
%for power measurement, use getPower.m with manual measurement as described
%in getPower.m help section
%pname = uigetfile('pwr_*.log', 'Open power data');
%if pname==0
%    return
%end
%dp=load(pname);

df=load(fname);

f=df(:,3);
t=df(:,7);
l=df(:,8:23); %start from core-2

% Show frequency:
%f1=figure();
%plot(f)

% Show loads:
%f2=figure();
%plot(l)

% Show temperature
f3=figure();
plot(t)
