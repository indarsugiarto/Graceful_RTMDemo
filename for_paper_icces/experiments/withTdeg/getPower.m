
function [avgTS, pA, pB, pS, pM, t] = getPower(fIn, withPlot)
% compute the power consumption from power data collected using Raspberry
% Pi. Output:
% pA = power in Bank A
% pB = power in Bank B
% pS = power in SDRAM
% pD = power in BMP
% t = sampling time
% avgTS = average time sampling
%
% Here is how I compute energy consumption for ICCES paper:
% close all; [ts,a] = getPower('pwr_user_200_jpge_xga.log', false); plot(a)
% then try to find the point for x
% x=[825,3904]; pA=a(x(1):x(2)); z=trapz(pA); ds=(x(2)-x(1))*ts; en=z*ds/3600


d=load(fIn);

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

% f = designfilt('lowpassfir', ...
%     'PassbandFrequency',0.001,'StopbandFrequency',0.04, ...
%     'PassbandRipple',1,'StopbandAttenuation',60, ...
%     'DesignMethod','equiripple');
% y = filtfilt(f,pA);


if withPlot

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
    %f5=figure('Color','w');
    %plot(t,y); title('Power Distribution Bank-A'); xlabel('Time (s)'); ylabel('Watt');
end
t0=d(1,9); tn=d(length(d),9); avgTS=(tn-t0)/length(d);
%fprintf('Average sampling time = %f-sec\n',avgTS);
%trapz(y)
end
