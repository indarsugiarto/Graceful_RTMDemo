
function n = temperature_conversion(fIn)

% The following is the result from t5-readT-calib:
%regCoef = [[[-5.653730, 49.735660, 6122.280178, 220.727814],
%[6.538217, 49.735660, 10480.087606, 610.975818],
%[-0.352222, 2.389128, -9.257577, 47.768628, 4912.135244, 2813.061969]],
%[[-5.588882, 47.380537, 5943.352039, 222.964395],
%[6.423523, 47.380537, 10385.116270, 618.201994],
%[-0.319137, 2.125303, -8.922037, 45.594551, 6518.740008, 3767.207430]],
%[[-4.737709, 43.407949, 6312.833670, 236.830829],
%[5.392405, 43.407949, 10581.910375, 617.655847],
%[-0.267238, 1.762617, -7.322483, 41.913838, 6782.597901, 3925.164153]],
%[[-5.232014, 44.860351, 6585.580945, 243.260153],
%[5.923378, 44.860351, 10945.630198, 621.112483],
%[-0.330129, 2.057306, -8.041973, 43.127229, 6639.769075, 3877.857287]]];

% For ICCES, since we work only with chip <0,0>, let's assume the chip
% characteristic is similar to that on Spin3. The polyfit coefficient 
% corresponds to sensor-1 and sensor-3 are:
c1_p = [-5.653730, 49.735660];
c1_mu = [6122.280178, 220.727814];
c3_p = [-0.352222, 2.389128, -9.257577, 47.768628];
c3_mu = [4912.135244, 2813.061969];

% Here is an example of how to use polyval. The temperature data is in column 7-8
% d=load('profiler_ondemand_edge_vga.log');
% t1 = d(:,7);
% t3 = d(:,8);
% 
% T1 = polyval(c1_p, t1, [], c1_mu);
% T3 = polyval(c3_p, t3, [], c3_mu);
% 
% x = 1:length(d);
% plot(x,T1,x,T3);

% Prepare the output format
fmt = '%d';
for i=1:5
    fmt = strcat(fmt, ',%d');
end
% just use T3, it is more reliable
fmt = strcat(fmt, ',%f');
% just use core-2 to core-18
for i=1:16
    fmt = strcat(fmt, ',%d');
end
% finally, the timestamp
fmt = strcat(fmt, ',%f\n');

% It should produce:
% '%d,%d,%d,%d,%d,%d,%f,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%f'

% First, load the data and process T3
d = load(fIn);
t3 = d(:,8);
T3 = polyval(c3_p, t3, [], c3_mu);

% Create the output file
fOut = strrep(fIn, '.log', '-Tdeg.log');
fid = fopen(fOut, 'wt');

n = length(d);

for i=1:n
    fprintf(fid, fmt, d(i,1), d(i,2), d(i,3), d(i,4), d(i,5), d(i,6),...
        T3(i), d(i,12), d(i,13), d(i,14), d(i,15), d(i,16), d(i,17),...
        d(i,18), d(i,19), d(i,20), d(i,21), d(i,22), d(i,23), d(i,24),...
        d(i,25),d(i,26),d(i,27),d(i,28));
end

fclose(fid);

fprintf('Processing %d-lines is done!\n', n);

end
