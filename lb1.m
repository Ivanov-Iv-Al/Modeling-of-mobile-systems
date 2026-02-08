message = 'Hello World! This is a test message.';
bits = sign_coder(message);
disp(['First 24 bits: ' num2str(bits(1:24)) '...']);
decoded = sign_decoder(bits);
disp(['Decoded: ' decoded]);

function bits = sign_coder(text_message)
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .';
    bits = [];
    
    for i = 1:length(text_message)
        idx = strfind(alphabet, text_message(i)) - 1;
        
        bit6 = [];
        for j = 5:-1:0
            bit_val = bitand(idx, 2^j) > 0;
            bit6 = [bit6 bit_val];
        end
        
        bits = [bits bit6];
    end
end

function text_message = sign_decoder(bits)
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .';
    text_message = '';
    
    for i = 1:6:length(bits)
        idx = 0;
        for j = 1:6
            idx = idx * 2 + bits(i+j-1);
        end
        
        text_message = [text_message alphabet(idx+1)];
    end
end
