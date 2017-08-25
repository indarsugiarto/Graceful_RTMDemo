f1 = load('profiler_user_200_edge_xga-Tdeg.log');
f2 = load('profiler_ondemand_edge_xga-Tdeg.log');
f3 = load('profiler_consv_edge_xga-Tdeg.log');
f4 = load('profiler_pmc_edge_xga-Tdeg.log');

t1=f1(:,7); t1=t1; t1(1:300)=[];
t2=f2(:,7); t2(1:650)=[];
t3=f3(:,7); t3=t3+0.2; t3(1:200)=[];
t4=f4(:,7); t4=t4-0.25; t4(1:50)=[];


% Show temperature
plot(t1,'b'); hold on;
plot(t2,'r');
plot(t3,'g');
plot(t4,'m');

xlabel('Timestep (ms)'); ylabel('Temperature (C-deg)');
xlim([3000,7000]);
legend('G1', 'G2', 'G3', 'G4');
