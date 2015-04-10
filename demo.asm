	cld
	mov esi, src
	mov edi, dst
	mov ecx, size
label1:
	mov al, [esi]
	inc al ; calculate
	mov [edi], al
	inc esi
	inc edi
	dec ecx
	jnz label1  ; loop to la
        ret