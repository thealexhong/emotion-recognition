function Features = stFeatureExtraction(signal, fs, win, step)

% function Features = stFeatureExtraction(signal, fs, win, step)
%
% This function computes basic audio feature sequencies for an audio
% signal, on a short-term basis.
%
% ARGUMENTS:
%  - signal:    the audio signal
%  - fs:        the sampling frequency
%  - win:       short-term window size (in seconds)
%  - step:      short-term step (in seconds)
%
% RETURNS:
%  - Features: a [MxN] matrix, where M is the number of features and N is
%  the total number of short-term windows. Each line of the matrix
%  corresponds to a seperate feature sequence
%
% (c) 2014 T. Giannakopoulos, A. Pikrakis

% if STEREO ...
if (size(signal,2)>1)
    signal = (sum(signal,2)/2); % convert to MONO
end

% convert window length and step from seconds to samples:
windowLength = round(win * fs);
step = round(step * fs);

curPos = 1;
L = length(signal);

% compute the total number of frames:
numOfFrames = floor((L-windowLength)/step) + 1;
% disp(strcat('Number of Frames', num2str(numOfFrames)));
% number of features to be computed:
numOfFeatures = 58;
Features = zeros(numOfFeatures, numOfFrames);
Ham = window(@hamming, windowLength);
mfccParams = feature_mfccs_init(windowLength, fs);

for i=1:numOfFrames % for each frame
    % get current frame:
    frame  = signal(curPos:curPos+windowLength-1);
    frame  = frame .* Ham;
    frameFFT = getDFT(frame, fs);
    
    if (sum(abs(frame))>eps)
        % compute time-domain features:
        Features(1,i) = feature_zcr(frame);
        Features(2,i) = feature_energy(frame);
        Features(3,i) = feature_energy_entropy(frame, 10);

        % compute freq-domain features: 
        if (i==1) frameFFTPrev = frameFFT; end;
        [SpecCentroid, SpecCentroidSpread] = ...
            feature_spectral_centroid(frameFFT, fs);
        Features(4,i) = SpecCentroid;
        Features(5,i) = SpecCentroidSpread;
        Features(6,i) = feature_spectral_entropy(frameFFT, 10);
        Features(7,i) = feature_spectral_flux(frameFFT, frameFFTPrev);
        Features(8,i) = feature_spectral_rolloff(frameFFT, 0.90);
        MFCCs = feature_mfccs(frameFFT, mfccParams);
        Features(9:28,i)  = MFCCs;
        
        [HR, F0] = feature_harmonic(frame, fs);
        Features(29, i) = HR;
        Features(30, i) = F0;
        ChromaVector = feature_chroma_vector(frame, fs);
        Features(31:42, i) = ChromaVector;
       
        LPC = feature_lpccs(frame);
        Features(43:58, i) = LPC(2:17);
        
    else
        Features(:,i) = zeros(numOfFeatures, 1);
    end    
    curPos = curPos + step;
    frameFFTPrev = frameFFT;
end
Features(58, :) = medfilt1(Features(58, :), 3);