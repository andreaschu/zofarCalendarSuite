# pip install python-snappy
import snappy
import sys

def hexdecode(input_str: str) -> bytes:
    return bytes.fromhex(input_str)


def hexdecode_and_decompress(input_str: str) -> str:
    return snappy.decompress(hexdecode(input_str)).decode('cp1252')


def hexencode(input_bytes: bytes) -> str:
    return input_bytes.hex()


def compress_and_hexencode(input_bytes: bytes) -> str:
    return hexencode(snappy.compress(input_bytes))


def main():
    input_str_compressed = r'c317f0585b7b2274657374766172303030223a2257656e6e206d616e2064696520616b7475656c6c656e2042756368756e67737a61686c656e20626574726163687465742c2064616e6e207769726b7420736f2065696e65207669727405397c20486175707476657273616d6d6c756e67206572737420726563687420776965012f7c2052656c696b7420617573206465722056657267616e67656e686569742e20440191018d344c75667468616e73612077696c6c051344436f726f6e612d50616e64656d6965206e6901587c6e757220236d656e74616c2068696e7465722073696368206c617373656e232c05795453706f68722073616774652c20736f6e6465726e206b01cb646469657320776f686c206175636820776972747363686166746c01450c7363686e21133c722065727265696368656e2c20616c730137f05e204b6f6e7a65726e73747261746567656e206572686f66667420686162656e2e204469652052fc636b6b656872207a756d204e61636866726167656e697665617520646573204a61687265732032303139206572776172746574656e207369212e0867656e09882066fc72204d697474651534547a65686e74732c20646f6368206e756e20676568742021520d9714206461766f6e2168142c206461737301cc386f6e20696d206b6f6d6d656e64656e057d011d402074696566652054616c20fc6265727775051e4c7365696e206bf66e6e74652e20496d206c6175661d380c776972642908186170617a6974e421d54c662037352050726f7a656e7420686f636867656601e21c6e2c20656e747370410c1c656e642073696e6429726c64726569205669657274656c20616c6c657220466c75677a6575676521bc01d324696d2045696e7361747a2956205a69656c6d61726b6525190c32303233095104736301e300391582082e222c59f00031fef002fef002fef002fef002fef002fef002fef002fef002fef002fef002fef002baf0020032fef002fef002fef002fef002fef002fef002fef002fef002fef002fef002fef002baf0020033fef002fef002fef002fef002fef002fef002fef002fef002fef002fef002fef0028ef002047d5d'
    input_str_raw = r'[{"testvar000":"Wenn man die aktuellen Buchungszahlen betrachtet, dann wirkt so eine virtuelle Hauptversammlung erst recht wie ein Relikt aus der Vergangenheit. Denn die Lufthansa will die Corona-Pandemie nicht nur #mental hinter sich lassen#, wie Spohr sagte, sondern kann dies wohl auch wirtschaftlich schneller erreichen, als die Konzernstrategen erhofft haben. Die Rückkehr zum Nachfrageniveau des Jahres 2019 erwarteten sie eigentlich für Mitte des Jahrzehnts, doch nun geht der Konzern davon aus, dass schon im kommenden Jahr das tiefe Tal überwunden sein könnte. Im laufenden Jahr wird die Kapazität auf 75 Prozent hochgefahren, entsprechend sind auch drei Viertel aller Flugzeuge wieder im Einsatz. Die Zielmarke für 2023 sind schon 95 Prozent.","testvar001":"Wenn man die aktuellen Buchungszahlen betrachtet, dann wirkt so eine virtuelle Hauptversammlung erst recht wie ein Relikt aus der Vergangenheit. Denn die Lufthansa will die Corona-Pandemie nicht nur #mental hinter sich lassen#, wie Spohr sagte, sondern kann dies wohl auch wirtschaftlich schneller erreichen, als die Konzernstrategen erhofft haben. Die Rückkehr zum Nachfrageniveau des Jahres 2019 erwarteten sie eigentlich für Mitte des Jahrzehnts, doch nun geht der Konzern davon aus, dass schon im kommenden Jahr das tiefe Tal überwunden sein könnte. Im laufenden Jahr wird die Kapazität auf 75 Prozent hochgefahren, entsprechend sind auch drei Viertel aller Flugzeuge wieder im Einsatz. Die Zielmarke für 2023 sind schon 95 Prozent.","testvar002":"Wenn man die aktuellen Buchungszahlen betrachtet, dann wirkt so eine virtuelle Hauptversammlung erst recht wie ein Relikt aus der Vergangenheit. Denn die Lufthansa will die Corona-Pandemie nicht nur #mental hinter sich lassen#, wie Spohr sagte, sondern kann dies wohl auch wirtschaftlich schneller erreichen, als die Konzernstrategen erhofft haben. Die Rückkehr zum Nachfrageniveau des Jahres 2019 erwarteten sie eigentlich für Mitte des Jahrzehnts, doch nun geht der Konzern davon aus, dass schon im kommenden Jahr das tiefe Tal überwunden sein könnte. Im laufenden Jahr wird die Kapazität auf 75 Prozent hochgefahren, entsprechend sind auch drei Viertel aller Flugzeuge wieder im Einsatz. Die Zielmarke für 2023 sind schon 95 Prozent.","testvar003":"Wenn man die aktuellen Buchungszahlen betrachtet, dann wirkt so eine virtuelle Hauptversammlung erst recht wie ein Relikt aus der Vergangenheit. Denn die Lufthansa will die Corona-Pandemie nicht nur #mental hinter sich lassen#, wie Spohr sagte, sondern kann dies wohl auch wirtschaftlich schneller erreichen, als die Konzernstrategen erhofft haben. Die Rückkehr zum Nachfrageniveau des Jahres 2019 erwarteten sie eigentlich für Mitte des Jahrzehnts, doch nun geht der Konzern davon aus, dass schon im kommenden Jahr das tiefe Tal überwunden sein könnte. Im laufenden Jahr wird die Kapazität auf 75 Prozent hochgefahren, entsprechend sind auch drei Viertel aller Flugzeuge wieder im Einsatz. Die Zielmarke für 2023 sind schon 95 Prozent."}]'

    decompressed1 = hexdecode_and_decompress(input_str_compressed)
    recompressed1 = compress_and_hexencode(decompressed1.encode('cp1252'))
    redecompressed1 = hexdecode_and_decompress(recompressed1)

    assert input_str_raw == decompressed1
    assert input_str_raw == redecompressed1
    try:
        assert recompressed1 == input_str_compressed
    except AssertionError as e:
        a = [i for i in range(min(len(input_str_compressed), len(recompressed1))) if input_str_compressed[i] != recompressed1[i]]
        # breakpoint()



    compressed2 = compress_and_hexencode(input_str_raw.encode('cp1252'))
    decompressed2 = hexdecode_and_decompress(compressed2)
    try:
        assert decompressed2 == input_str_raw
    except AssertionError as e:
        a = [i for i in range(min(len(input_str_raw), len(decompressed2))) if
             input_str_raw[i] != decompressed2[i]]
        breakpoint()

    try:
        assert compressed2 == input_str_compressed
    except AssertionError as e:
        a = [i for i in range(min(len(input_str_compressed), len(compressed2))) if
             input_str_compressed[i] != compressed2[i]]
        breakpoint()
    breakpoint()


if __name__ == '__main__':
    # print(compress_and_hexencode('[{"TypA":{"split_var":[{"splitvar01":"ao1"}],"timestamp_var":"splittimestamp01"},"TypB":{"split_var":[{"splitvar02":"ao1"}],"timestamp_var":"splittimestamp02"},"TypC":{"split_var":[{"vaa14XX":"ao1"}],"timestamp_var":"vaa15splitDateXX"}}]'.encode('utf-8')))
    # print(hexdecode_and_decompress('db01c85b7b2254797041223a7b2273706c69745f766172223a5b7b227661613130223a22616f31227d5d2c2274696d657374616d705f05220520003105331844617465227d2c0148004256480000327a480000333e4800004356480000347a4800343573706c697444617465227d7d5d'))
    main()

    print(hexdecode_and_decompress(''))
