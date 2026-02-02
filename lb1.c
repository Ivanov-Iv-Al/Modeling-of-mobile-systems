#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define BITS 6 

char* sign_encoder(const char* text) {
    if (!text) return NULL;
    int len = strlen(text);
    if (len < 30 || len > 100) return NULL;
    
    char* bits = malloc(len * BITS + 1);
    if (!bits) return NULL;
    
    for (int i = 0; i < len; i++) {
        char c = text[i];
        int code;
        
        if (c >= 'A' && c <= 'Z') code = c - 'A';
        else if (c >= 'a' && c <= 'z') code = c - 'a' + 26;
        else if (c >= '0' && c <= '9') code = c - '0' + 52;
        else if (c == ' ') code = 62;
        else if (c == '.') code = 63;
        else { free(bits); return NULL; }
        
        for (int j = 0; j < BITS; j++) {
            bits[i * BITS + j] = (code >> (BITS - 1 - j)) & 1 ? '1' : '0';
        }
    }
    bits[len * BITS] = '\0';
    return bits;
}

char* sign_decoder(const char* bits) {
    if (!bits) return NULL;
    int bit_len = strlen(bits);
    if (bit_len % BITS != 0) return NULL;
    
    int len = bit_len / BITS;
    char* text = malloc(len + 1);
    if (!text) return NULL;
    
    for (int i = 0; i < len; i++) {
        int code = 0;
        
        for (int j = 0; j < BITS; j++) {
            code <<= 1;
            code |= (bits[i * BITS + j] == '1');
        }
        
        if (code < 26) text[i] = 'A' + code;
        else if (code < 52) text[i] = 'a' + (code - 26);
        else if (code < 62) text[i] = '0' + (code - 52);
        else if (code == 62) text[i] = ' ';
        else if (code == 63) text[i] = '.';
        else { free(text); return NULL; }  
    }
    text[len] = '\0';
    return text;
}

int check_alphabet(const char* text) {
    for (int i = 0; text[i]; i++) {
        char c = text[i];
        if (!((c >= 'A' && c <= 'Z') || 
              (c >= 'a' && c <= 'z') || 
              (c >= '0' && c <= '9') || 
              c == ' ' || c == '.')) return 0;
    }
    return 1;
}

int main() {
    const char* msg = "Hello World. This is test message and no more";
    printf("Исходное: %s\n\n", msg);
    
    if (!check_alphabet(msg)) {
        printf("Неверный алфавит\n");
        return 1;
    }
    
    char* encoded = sign_encoder(msg);
    if (!encoded) {
        printf("Ошибка кодирования\n");
        return 1;
    }
    printf("Закодировано: %s\n\n", encoded);
    
    char* decoded = sign_decoder(encoded);
    if (!decoded) {
        printf("Ошибка декодирования\n");
        free(encoded);
        return 1;
    }
    printf("Декодировано: %s\n\n", decoded);
    
    if (strcmp(msg, decoded) == 0) printf("Декодирование завершено\n");
    else printf("Ошибка декодирования\n");
    
    free(encoded);
    free(decoded);
    return 0;
}