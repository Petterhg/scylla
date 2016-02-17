/*
 * Copyright (C) 2015 Cloudius Systems, Ltd.
 */

/*
 * This file is part of Scylla.
 *
 * Scylla is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Scylla is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Scylla.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "db/serializer.hh"
#include "frozen_mutation.hh"
#include "mutation_partition.hh"
#include "mutation.hh"
#include "partition_builder.hh"
#include "mutation_partition_serializer.hh"
#include "utils/UUID.hh"
#include "utils/data_input.hh"
#include "query-result-set.hh"

//
// Representation layout:
//
// <mutation> ::= <column-family-id> <schema-version> <partition-key> <partition>
//

using namespace db;

utils::UUID
frozen_mutation::column_family_id() const {
    data_input in(_bytes);
    return uuid_serializer::read(in);
}

utils::UUID
frozen_mutation::schema_version() const {
    data_input in(_bytes);
    uuid_serializer::skip(in); // cf_id
    return uuid_serializer::read(in);
}

partition_key_view
frozen_mutation::key(const schema& s) const {
    data_input in(_bytes);
    uuid_serializer::skip(in); // cf_id
    uuid_serializer::skip(in); // schema_version
    return partition_key_view_serializer::read(in);
}

dht::decorated_key
frozen_mutation::decorated_key(const schema& s) const {
    return dht::global_partitioner().decorate_key(s, key(s));
}

frozen_mutation::frozen_mutation(bytes&& b)
    : _bytes(std::move(b))
{ }

frozen_mutation::frozen_mutation(const mutation& m) {
    auto&& id = m.schema()->id();
    partition_key_view key_view = m.key();
    auto version = m.schema()->version();

    uuid_serializer id_ser(id);
    uuid_serializer schema_version_ser(version);
    partition_key_view_serializer key_ser(key_view);
    mutation_partition_serializer part_ser(*m.schema(), m.partition());

    bytes_ostream out;
    id_ser.write(out);
    schema_version_ser.write(out);
    key_ser.write(out);
    part_ser.write(out);

    auto bv = out.linearize();
    _bytes = bytes(bv.begin(), bv.end()); // FIXME: avoid copy
}

mutation
frozen_mutation::unfreeze(schema_ptr schema) const {
    mutation m(key(*schema), schema);
    partition_builder b(*schema, m.partition());
    partition().accept(*schema, b);
    return m;
}

frozen_mutation freeze(const mutation& m) {
    return { m };
}

mutation_partition_view frozen_mutation::partition() const {
    data_input in(_bytes);
    uuid_serializer::skip(in); // cf_id
    uuid_serializer::skip(in); // schema_version
    partition_key_view_serializer::skip(in);
    return mutation_partition_view::from_bytes(in.read_view(in.avail()));
}

std::ostream& operator<<(std::ostream& out, const frozen_mutation::printer& pr) {
    return out << pr.self.unfreeze(pr.schema);
}

frozen_mutation::printer frozen_mutation::pretty_printer(schema_ptr s) const {
    return { *this, std::move(s) };
}
