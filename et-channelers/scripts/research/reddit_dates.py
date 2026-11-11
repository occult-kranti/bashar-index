from datetime import date, timedelta
def b36(s): return int(s,36)
anchors=[("f1kja5",date(2020,2,10)),("nsfbdz",date(2021,6,4)),("yw6acb",date(2022,11,16)),("10c0t7g",date(2023,1,14)),("1abacyq",date(2024,1,25)),("1h9dlvg",date(2024,12,8)),("1l1jk6o",date(2025,6,2)),("1x8sqam",date(2026,10,18))]
an=[(b36(a),d) for a,d in anchors]
def est(pid):
    v=b36(pid)
    for (v1,d1),(v2,d2) in zip(an,an[1:]):
        if v1<=v<=v2:
            f=(v-v1)/(v2-v1); return d1+timedelta(days=f*(d2-d1).days)
    if v<an[0][0]:
        (v1,d1),(v2,d2)=an[0],an[1]
    else:
        (v1,d1),(v2,d2)=an[-2],an[-1]
    rate=(d2-d1).days/(v2-v1); return d1+timedelta(days=(v-v1)*rate)
ids="""yw6acb f1kja5 fwltff 1bf9t1k 184czl0 1byy5yu 1cxuz6g 18y7r8o pezkoi 1c9s1e8 r52e5a 1e30rf5 55weh7 1kle5cu egkmjh
1abacyq 1l1jk6o 1ctgjro 17itfhk 1qxqvdr 1k2hsmu 1k1occq 1ibkwsg 1u5wky3 1w8aetd 1ehsggh 1edxsqv 1lyr483 1tjpn1w 1ke3r69 1fgmsn4 1u9qobv 1qwqaqd 17mf4ro 1d524p2 18e05hq nsfbdz pkygoa 1dw6x50
1ldpcbc 1te7db9 v4w8ki 1tfwvhs 1jfpd8e 15drdyr 1phcue6 1h9dlvg 12drnlo b8ngmy 13hkoyc a9qz4w b5ad7n 10zreok btucml dbvtwm 1e7uejs 1jwt2me 1sfhu69
1tqchak 1dt51jz 1cxohl3 1s8udce orirxp 1dnlxkv 1lltqw2 re8egh 1hrqy1o 1v7shel 1kfoctd 148owft 1ojgb7v
1kblw7p 1v9wflo 1agaysr 1cyjefh 1uwogfq 1wz9qhs voa362 1iyru3n q4i7ye
178tbu8 17eg9nz 1af69ec 1lvvjn7 178cykm 18cbl3z 1sbis7x 1p2guy0 1jtvwg2
1ppvpx8 1vswmsf 1m36na0 1snahva 173ni21 1lkzr6i 1dr6a3z 1tzia6t 1ozqkek 1r3902w 1tt16ig 1cjpnpx 1tjgmkx 1b9pkr5 18w0oxb
1idzt68 1w0smfi 1tzky5a 1qlg6iq 1jhrtvw 1sgm1hw rcb8lt 1qx4gib 1sn3tcz s0o564 1hj1qgd 1w95ari m28o3c 1vorsor 1oxge5c yel9ne
1w36w6p 1ql63r8 18swet5 1byv32h 1coua0x 1224hzn 1pi880k jxywr6 zi01mz 1bhuvyi
1i1x00e 1u0qqgl 1ibwjnb 135y205 1fkjvok 1gf8w6t 1e5b7wc 1ra7z90 1ibm0z6 1iiop87 1pvd7c2 ovvx4t
1g8b3ma 1j3fmf9 1wb7791 1p9dofq 1hfaa5t 1gww60l rrw0mo 120m956 1b1euvs 1cii443 1q4czj8 1onptkb 1t3ni9r 1dbvvhf 1loxca3
peu2os oqsbhb vvjobz 1o9cv53 10c0t7g 1kkeknu
1u21g23 1tc6h81 1tj3gvh jggyhi 1tb40wc 1thuhv7 1wv5n6d 1tu5eko
1i02jme 1x8sqam 1nt09mo 1x7q3qu 1pv4fvx xsahig 1jt1whm 1gyi0nx 1m8uast 1um7uze 1pdx3vm 1qpezra 1kcpt29 1mdhfdf 1uct5xt"""
for pid in ids.split():
    print(pid, est(pid).isoformat())
