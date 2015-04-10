		mov edi, ptr1;
		mov esi, ptr2;
		pxor mm7, mm7;		// mm7 = 0000....00
		pcmpeqb mm6, mm6;	// mm6 = ffff....ff
loop_line: 
		mov ecx, w;
		shr ecx, 1;
		ALIGN 8
loop_pixel_x2:
		prefetchnta [esi + 128];
		prefetchnta [edi + 128];
		movd mm0, [esi];
		movd mm1, [esi + 4];
		mov eax, [edi];
		mov ebx, [edi + 4];	//ddddddd
		movq mm2, mm0;
		movq mm3, mm1;
		psrlq mm2, 24;
		psrlq mm3, 24;
		punpcklwd mm2, mm2;
		punpcklwd mm3, mm3;
		punpckldq mm2, mm2;		// mm2 = 0 a1 0 a1 0 a1 0 a1 (word)
		punpckldq mm3, mm3;		// mm3 = 0 a2 0 a2 0 a2 0 a2 (word)
		pcmpeqb mm4, mm4;		// mm4 = 0xffff...ff
		pcmpeqb mm5, mm5;		// mm5 = 0xffff...ff
		punpcklbw mm0, mm7;		// mm0 = src1
		punpcklbw mm1, mm7;		// mm1 = src2
		punpcklbw mm4, mm7;
		punpcklbw mm5, mm7;
		psubb mm4, mm2;			// mm4 = (0xff - a1)...
		psubb mm5, mm3;			// mm5 = (0xff - a2)...

		pmullw mm0, mm2;		// mm0 = src1 * alpha1
		pmullw mm1, mm3;		// mm1 = src2 * alpha2
		movd mm2, eax;			// mm2 = dst1
		movd mm3, ebx;			// mm3 = dst2
		punpcklbw mm2, mm7;
		punpcklbw mm3, mm7;
		pmullw mm2, mm4;		// mm2 = dst1 * (255 - a1)
		pmullw mm3, mm5;		// mm3 = dst2 * (255 - a2)

		pcmpeqw mm5, mm5;
		punpcklbw mm5, mm7;

		paddw mm0, mm2;
		paddw mm1, mm3;
		psrlw mm0, 8;
		psrlw mm1, 8;
		pand mm0, mm5;
		pand mm1, mm5;
		packuswb mm0, mm0;
		packuswb mm1, mm1;

		movd [edi], mm0;
		movd [edi + 4], mm1;

		add edi, 8;
		add esi, 8;
		dec ecx;
		jnz loop_pixel_x2;

		mov ecx, w;
		and ecx, 1;
		cmp ecx, 0;
		jz end_line;
		
		// last single pixel
		movd mm0, [esi];
		mov eax, [edi];
		movq mm2, mm0;
		psrlq mm2, 24;
		punpcklwd mm2, mm2;
		punpckldq mm2, mm2;		// mm2 = 0 a1 0 a1 0 a1 0 a1 (word)
		pcmpeqb mm4, mm4;		// mm4 = 0xffff...ff
		punpcklbw mm0, mm7;		// mm0 = src1
		punpcklbw mm4, mm7;
		psubb mm4, mm2;			// mm4 = (0xff - a1)...
		pmullw mm0, mm2;		// mm0 = src1 * alpha1
		movd mm2, eax;			// mm2 = dst1
		punpcklbw mm2, mm7;
		pmullw mm2, mm4;		// mm2 = dst1 * (255 - a1)
		pcmpeqw mm5, mm5;
		punpcklbw mm5, mm7;
		paddw mm0, mm2;
		psrlw mm0, 8;
		packuswb mm0, mm0;
		movd [edi], mm0;
		add esi, 4;
		add edi, 4;
		jmp end_line
		jmp end_line
end_line:
		add edi, diff1;
		add esi, diff2;
		dec dword ptr h;
		push word ptr w;
		pop word ptr w;
		jnz loop_line;
nop: nop
		db 1,2
		mov byte ptr[edi], 0
		mov word ptr[edi], 0
		mov dword ptr[edi], 0
		mov eax, word ptr[edi]
		push ax
		emms;
