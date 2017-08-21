% biru: 3750 2048
% brown: 3750 1024
% pink: 3750 512
% green: 3750 1024 with 1-5 delay
% 
% better: 3750 2380 with 1-5 delay, gives 0.644704-msec sapling period
% 
% Kesimpulan: 3750 1024 dengan delay poweroff min 10

%d=load('va_benchmark_7500_10s.log');
%d=load('cek_on_off.log');
%d=load('va_benchmark_7500_15s.log');
%d=load('pt_demo2.log');

% Remove the last line in dataset
%dname='LGN_30s_on_3750sps_scale10.log';
%command = sprintf('./preprocess %s',dname);
%system(command);

%dname = 'BG_on_7500sps.log';
dname = 'BG_on_3750sps.log';
%dname = 'BG_on_10sps.log';
%dname = 'BG_on_2000sps.log';
%dname = 'BG3_on_3750sps.log';
d=load(dname);

%Somehow, some data are arrives before the previous one!!!
%d=sortrows(b,9); --> WRONG!!!

iA = d(:,1);
vA = d(:,2);
iB = d(:,3);
vB = d(:,4);
iS = d(:,5);
vS = d(:,6);
iM = d(:,7);
vM = d(:,8);
ts = d(:,9);
pA = zeros(length(d),1);
pB = zeros(length(d),1);
pS = zeros(length(d),1);
pM = zeros(length(d),1);
st = zeros(length(d),1); %sampling time in sec
t  = zeros(length(d),1);

for i=1:length(d)
    %catatanku: 4.1943==3.3*1.271==5.0*0.83886, dan 4194304==16777216*0.005*50

    pA(i) = ((iA(i)*4.1943/4194304)/(0.005*50))*(vA(i)*4.1943/4194304);
    pB(i) = ((iB(i)*4.1943/4194304)/(0.005*50))*(vB(i)*4.1943/4194304);
    pS(i) = ((iS(i)*4.1943/4194304)/(0.005*50))*(vS(i)*4.1943/4194304);
    %The following is without compensation with 2/3 because we don't use
    %any voltage divider:
    pM(i) = ((iM(i)*4.1943/4194304)/(0.010*50))*(vM(i)*4.1943/4194304);
    %In the sketch program using processing, there's 2/3 factor for the BMP:
    %pM(i) = ((iM(i)*4.1943/4194304)/(0.010*50))*(0.67*vM(i)*4.1943/4194304);
    if i ~= 1
        st(i) = ts(i)-ts(i-1);
        t(i) = ts(i)-ts(1);
        %if(ts(i)<ts(i-1))
        %    disp('Found mis...')
        %end
    end
end

mt = mean(st);
for i=2:length(d)
    %t(i) = t(i-1)+mt;
end

%I[i] = (float(I1[i])*4.1943/4194304)/(0.005*50)
%        V[i] = (float(V1[i])*4.1943/4194304)
%        V33[i] = (float(V3[i])*4.1943/4194304)
f0=figure('Color','w');
plot(t,pA,t,pB,t,pS,t,pM,'LineWidth',2); title('Power Distribution'); xlabel('Time (s)'); ylabel('Watt');
legend('Bank-A','Bank-B','SDRAM','BMP');
f1=figure('Color','w');
plot(t,pA); title('Power Distribution Bank-A'); xlabel('Time (s)'); ylabel('Watt');
f2=figure('Color','w');
plot(t,pB); title('Power Distribution Bank-B'); xlabel('Time (s)'); ylabel('Watt');
f3=figure('Color','w');
plot(t,pS); title('Power for SDRAM'); xlabel('Time (s)'); ylabel('Watt');
f4=figure('Color','w');
plot(t,pM); title('Power for BMP'); xlabel('Time (s)'); ylabel('Watt');
f5=figure('Color','w');
bar(st); title(sprintf('Sampling Time (average==%f)',mean(st))); 
t0=d(1,9); tn=d(length(d),9); s=(tn-t0)/length(d);
fprintf('Average sampling time = %f-msec\n',s*1000);
