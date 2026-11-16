#!/usr/bin/env python3
"""Independently count curve points and expand the eta product using integers.

This finite verification is not a proof of modularity or of a Langlands conjecture.
Only the Python standard library is required.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def is_prime(n:int)->bool:
    return n>=2 and all(n%d for d in range(2,int(n**.5)+1))

def points(p:int)->list[tuple[int,int]]:
    if not is_prime(p) or p==2:
        raise ValueError('This example requires an odd prime (good reduction).')
    return [(x,y) for x in range(p) for y in range(p) if (y*y-x*x*x+x)%p==0]

def point_count(p:int)->int:
    # The point at infinity must be included.
    return len(points(p))+1

def eta_product_coefficients(limit:int)->list[int]:
    """Coefficients of q*prod((1-q^(4n))^2*(1-q^(8n))^2), through q^limit."""
    if limit<1:raise ValueError('limit must be positive')
    c=[0]*(limit+1);c[0]=1
    for multiplier in (4,8):
        for k in range(multiplier,limit+1,multiplier):
            for _ in range(2):
                for j in range(limit,k-1,-1):
                    c[j]-=c[j-k]
    return [0]+c[:limit]

def verify(limit:int=199)->dict:
    b=eta_product_coefficients(limit)
    rows=[]
    for p in range(3,limit+1,2):
        if not is_prime(p):continue
        count=point_count(p);a=p+1-count
        if a!=b[p]:raise AssertionError(f'p={p}: curve coefficient {a} != eta coefficient {b[p]}')
        rows.append({'p':p,'point_count_including_infinity':count,'a_p':a,'b_p':b[p],'match':True})
    assert points(5)==[(0,0),(1,0),(2,1),(2,4),(3,2),(3,3),(4,0)]
    expected={3:(4,0),5:(8,-2),7:(8,0),11:(12,0),13:(8,6),17:(16,2)}
    for p,(count,a) in expected.items():
        assert point_count(p)==count and p+1-count==a
    published_nonzero={1:1,5:-2,9:-3,13:6,17:2,25:-1,29:-10,37:-2,41:10,45:6,
                       49:-7,53:14,61:-10,65:-12,73:-6,81:9,85:-4,89:10,97:18}
    for n in range(1,min(limit,99)+1):assert b[n]==published_nonzero.get(n,0)
    # For p=5 and a_p=-2, det(I-A*T)=1-a_p*T+p*T^2.
    assert [1,-(-2),5]==[1,2,5]
    return {'curve':'y^2 = x^3 - x','eta_product':'q*prod_(n>=1) (1-q^(4n))^2 (1-q^(8n))^2',
            'prime_bound':limit,'checked_odd_primes':len(rows),'all_match':True,
            'point_count_5':8,'points_5_affine':points(5),'rows':rows,
            'limitation':'Finite independent numerical verification; NOT a proof of the theorem.'}

def main()->None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--limit',type=int,default=199)
    p.add_argument('--output',default='verification.json');a=p.parse_args()
    if a.limit<17:raise SystemExit('Use --limit >=17 for the displayed examples.')
    result=verify(a.limit)
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"PASS: all {result['checked_odd_primes']} odd primes <= {a.limit}; #E(F_5)=8, a_5=-2.")
    print('This finite check is not a proof.')
if __name__=='__main__':main()
